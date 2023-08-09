#!/bin/sh

# Estando seguro que las credenciales estan en ~/.aws/credentials

# Crear variables de entrada
model_name="linguo_test"
version="0.0.3"
rol_sagemaker="arn:aws:iam::312260343777:role/service-role/AmazonSageMaker-ExecutionRole-20230803T104880"
instance="ml.t2.medium"

# Function to display usage
usage() {
  echo "Usage: $0 -m <model_name> -v <version_with_dots> -r <rol_sagemaker> -i <instance>"
  exit 1
}

# Parse the command-line options using getopts
while getopts ":m:v:r:i:" opt; do
  case $opt in
    m) model_name="$OPTARG" ;;
    v) version="$OPTARG" ;;
    r) rol_sagemaker="$OPTARG" ;;
    i) instance="$OPTARG" ;;
    \?) echo "Invalid option -$OPTARG" >&2
        usage ;;
    :) echo "Option -$OPTARG requires an argument" >&2
       usage ;;
  esac
done

# Check if all required arguments are provided
# TODO: Se debe evaluar si role
echo "Checking arguments required"
if [ -z "$model_name" ] || [ -z "$version" ] || [ -z "$rol_sagemaker" ] || [ -z "$instance" ]; then
  echo "All arguments are required."
  usage
fi

# Extract the profile and region using grep and awk
credentials_file="$HOME/.aws/credentials"
profile=$(grep -oP "(?<=^\[).*(?=\])" "$credentials_file" | awk 'NR==1')
region=$(awk -F'=' '/region/{print $2; exit}' "$credentials_file")
profile_number=$(echo "$profile" | cut -d'_' -f1)

# Algunos calculos
aws_model_name=$(echo "$model_name-v$version" | tr '._' '-')

# 1. Crear imagen docker
echo "Building docker image"
docker build -t $model_name:$version .
wait

# 2. Subir imagen docker
echo "creating AWS ECR repository"
aws ecr create-repository \
  --repository-name $model_name \
  --region $region \
  --profile $profile
wait

# TODO: Mejor obtenerlo de la salida anterior
ecr=$profile_number.dkr.ecr.us-east-2.amazonaws.com
ecr_repo=$ecr/$model_name:$version

echo "Creating tag locally for ECR"
docker tag $model_name:$version $ecr_repo
wait

echo "Preparing login to upload image to AWS ECR"
password=$(aws ecr get-login-password --region $region --profile $profile)
docker login \
  -u AWS \
  -p $password $ecr
wait

echo "Uploading image to ECR repo"
docker push $ecr_repo
wait


# 3. Crear modelo. Ojo! debe crear un rol-arn con permisos sobre sagemaker
echo "Creating model in sagemaker"
aws sagemaker create-model \
  --model-name $aws_model_name \
  --primary-container Image=$ecr_repo \
  --execution-role-arn $rol_sagemaker \
  --profile $profile
wait


# 4. Configuracion endpoint
echo "Creating sagemaker endpoint configuration"
aws sagemaker create-endpoint-config \
  --endpoint-config-name $aws_model_name \
  --production-variants VariantName=$aws_model_name,ModelName=$aws_model_name,InitialInstanceCount=1,InstanceType=$instance \
  --profile $profile
wait


# 5. Despliegue endpoint
echo "Deploying sagemaker endpoint"
aws sagemaker create-endpoint \
  --endpoint-name $aws_model_name \
  --endpoint-config-name $aws_model_name \
  --profile $profile

aws sagemaker describe-endpoint \
  --endpoint-name $aws_model_name \
  --profile $profile

