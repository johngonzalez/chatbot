# Importa las bibliotecas necesarias
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from fastapi import FastAPI
from get_response import get_response_from_query
import uvicorn
import os
import boto3
import uuid
from datetime import datetime as dt

from dotenv import load_dotenv
load_dotenv()


def save_QA_dynamodb(dynamo_table, pregunta, respuesta):
    item = {
        "id": str(uuid.uuid4()),
        "datetime": dt.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "pregunta": pregunta,
        "respuesta": respuesta,
    }
    dynamo_response = dynamo_table.put_item(Item=item)
    return dynamo_response


# Crea la instancia de FastAPI
app = FastAPI()
db = FAISS.load_local('output/embeddings_faiss_index', OpenAIEmbeddings())

# Configura el cliente de DynamoDB usando las credenciales de AWS desde las variables de entorno
session = boto3.Session(
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)

dynamodb = session.resource("dynamodb")
dynamo_table = dynamodb.Table("chatbot")


# Define la ruta y función de la API para realizar preguntas
@app.get("/preguntar/{pregunta}")
async def preguntar(pregunta: str):
    respuesta = get_response_from_query(db, pregunta)
    # Almacena la pregunta y la respuesta en DynamoDB
    dynamo_out = save_QA_dynamodb(dynamo_table, pregunta, respuesta)
    print('Respuesta dynamo:', dynamo_out)
    return {"pregunta": pregunta, "respuesta": respuesta}


# Define la función principal para ejecutar la aplicación con uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
