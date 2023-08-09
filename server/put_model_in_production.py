import docker
import os
import boto3
from botocore.exceptions import ClientError
import base64
import click


def build_docker_image(image_name, dockerfile_path, dockerfile):
    client = docker.from_env()
    image, build_log = client.images.build(path=dockerfile_path, dockerfile=dockerfile, tag=image_name)
    for line in build_log:
        print(line)


def get_ecr_login_password(region, registry_id, boto3_session):

    ecr_client = boto3_session.client('ecr', region_name=region)

    try:
        token = ecr_client.get_authorization_token(registryIds=[registry_id])
        username, password = (
            base64.b64decode(token['authorizationData'][0]['authorizationToken'])
            .decode()
            .split(':')
        )
        return username, password
    
    except ClientError as e:
        print("Failed to get ECR login password:", e)
        return None, None


def push_image_to_ecr(source_image, target_image, region, registry_id, boto3_session):
    docker_client = docker.from_env()

    # Authenticate Docker with ECR
    username, password = get_ecr_login_password(region, registry_id, boto3_session)
    if username and password:
        auth_config = {"username": username, "password": password}
        # docker_client.login(**auth_config, registry=registry_id)

        # Tag the image with ECR registry URL
        docker_client.images.get(source_image).tag(target_image)
        ecr_client = boto3_session.client('ecr', region_name=region)
        repo_name = source_image.split(':')[0]

        # Push the image to ECR
        try:
            # TODO: Es posible que el usuario quiera utilizar un repo ya creado
            try:
                ecr_client.create_repository(repositoryName=source_image.split(':')[0])
                print(f"Created AWS ECR repository: {repo_name}")
            except:
                print(f'Respository {repo_name} already exists!')
                None
            print("Pushing AWS ECR in repository")
            docker_client.images.push(target_image, auth_config=auth_config)
            print("Image pushed to ECR successfully.")
        except docker.errors.APIError as e:
            print("Failed to push image to ECR:", e)
    else:
        print("Failed to authenticate with ECR.")


@click.command()
@click.option('--model', help='Model Name. Example: linguo_test_3', required=True)
@click.option('--version', default='latest', help='Model version. Example: 0.0.3')
@click.option('--rol', help='arn rol sagemaker. Example: arn:aws:iam::312260343777:role/service-role/AmazonSageMaker-ExecutionRole-20230803T104880', required=True)
@click.option('--instance', help='ec2 type instance. Example: ml.t2.medium', required=True)
@click.option('--profile', help='AWS credentials profile. Be sure have ~/.aws/credentials and ~/.aws/config. example: 312260343777_adl-shared-access-dev', required=True)

def main(model, version, rol, instance, profile):
    profile = '312260343777_adl-shared-access-dev'
    session = boto3.session.Session(profile_name=profile)
    credentials = session.get_credentials()
    # region = session.region_name
    region = 'us-east-2'
    print(session)
    print('='*80 +'\n', model, version, rol, instance, profile, region)

    registry_id = profile.split('_')[0]
    source_image_name = model + ':' + version    
    target_image = f'{registry_id}.dkr.ecr.{region}.amazonaws.com/{model}:{version}'
    dockerfile_path = os.getcwd()  # Path to the Dockerfile
    dockerfile = 'Dockerfile'

    # Step 1: Build Docker image
    print("Building Docker image... (wait some minutes)")
    build_docker_image(source_image_name, dockerfile_path, dockerfile)

    # Step 2: Tag and Push Docker image
    print("Tagging and pushing Docker image... (wait some minutes)")
    push_image_to_ecr(source_image_name, target_image, region, registry_id, session)

    # Step 3: Create Sagemaker model
    aws_model_name = "{}-v{}".format(model, version).replace('.', '-').replace('_', '-')
    sagemaker_client = session.client('sagemaker', region_name=region)
    
    print("Creating model in Sagemaker")
    sagemaker_client.create_model(ModelName=aws_model_name, PrimaryContainer={'Image': target_image}, ExecutionRoleArn=rol)
    print("Model created")

    # Step 4: Create Sagemaker endpoint configuration
    print("Creating Sagemaker endpoint configuration")
    sagemaker_client.create_endpoint_config(
        EndpointConfigName=aws_model_name,
        ProductionVariants=[{
            'VariantName': aws_model_name,
            'ModelName': aws_model_name,
            'InitialInstanceCount': 1,
            'InstanceType': instance
        }]
    )
    print("Configuration end point created")


    # Step 5. Create endpoint
    # print("Deploying sagemaker endpoint")
    # sagemaker_client.create_endpoint(EndpointName=aws_model_name, EndpointConfigName=aws_model_name)
    # print("Endpoint deploying ...")

    # Step 5: Update endpoint
    print('Updating sagemaker endpoint')
    # last_version = '0.0.3'
    # last_aws_model_name = "{}-v{}".format(model, last_version).replace('.', '-').replace('_', '-')
    last_aws_model_name = 'anly-linguo-serverless-v0-0-3'  # Si se quiere actualizar un modelo esto debería ser un parámetro 
    sagemaker_client.update_endpoint(EndpointName=last_aws_model_name, EndpointConfigName=aws_model_name)

if __name__ == "__main__":
    """
    Este script está en construcción. Roadmap:
    1. Lógica para actualizar modelo. Debe tener en cuenta la versión que se quiere actualizar
    2. No es sano guardar tantos modelos y configuraciones de endpoint, es posible actualizarlos también?
    3. Se debería consumir algunas cosas desde s3 como la configuración del modelo

    """
    main()
