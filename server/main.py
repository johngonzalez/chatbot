# Importa las bibliotecas necesarias
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from get_response import get_response_from_query
import uvicorn
import os
import boto3
from uuid import uuid4
from datetime import datetime as dt
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel
from botocore.exceptions import ClientError
from langchain.schema import (
    HumanMessage,
    SystemMessage,
    AIMessage
)


class Message(BaseModel):
    session_id: Optional[str] = None
    id: Optional[str] = None
    datetime: Optional[str] = None
    tokens_query: Optional[int] = None
    tokens_respo: Optional[int] = None
    text: str
    sender: str = 'user'


load_dotenv()


def save_QA_dynamodb(dynamo_table, messages):
    for message in messages:
        item = {
            "id": str(message['id']),
            "datetime": message['datetime'],
            "session_id": str(message['session_id']),
            "text": message['text'],
            "sender": message['sender'],
        }
        # dynamo_response = dynamo_table.put_item(Item=item)
        try:
            dynamo_response = dynamo_table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(id)'
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(
                    f"El mensaje con id {message['id']} ya existe en la base de datos.")
            else:
                raise e
    return dynamo_response


def set_messages_to_chat(messages):
    message_history = []
    for message in messages:
        message_chat = {
            'content': message.text,
            'additional_kwargs':  {
                key: value
                for key, value in {
                    'id': message.id,
                    'datetime': message.datetime,
                    'session_id': message.session_id,
                }.items()
                if value is not None
            }
        }
        if message.sender == 'system':
            message_chat = SystemMessage(**message_chat)
        elif message.sender == 'user':
            message_chat = HumanMessage(**message_chat)
        elif message.sender == 'ai':
            message_chat = AIMessage(**message_chat)
            # if hasattr(message, 'tokens_query'):
            #     message_chat.additional_kwargs['tokens_query'] = message.tokens_query
            # if hasattr(message, 'tokens_respo'):
            #     message_chat.additional_kwargs['tokens_respo'] = message.tokens_respo
        else:
            raise ValueError('sender should be "system", "user" or "ai"')
        message_history.append(message_chat)
    return message_history


def set_messages_to_api(messages):
    message_history = []
    for message in messages:
        message_api = {
            'id': message.additional_kwargs['id'],
            'datetime': message.additional_kwargs['datetime'],
            'session_id': message.additional_kwargs['session_id'],
            'text': message.content,
        }

        if isinstance(message, SystemMessage):
            message_api['sender'] = 'system'
        elif isinstance(message, HumanMessage):
            message_api['sender'] = 'user'
        elif isinstance(message, AIMessage):
            message_api['sender'] = 'ai'
            if 'tokens_query' in message.additional_kwargs:
                message_api['tokens_query'] = message.additional_kwargs['tokens_query']
            if 'tokens_respo' in message.additional_kwargs:
                message_api['tokens_respo'] = message.additional_kwargs['tokens_respo']
        else:
            raise ValueError(
                'message should be instance of "SystemMessage", "HumanMessage" or "AIMessage"')
        message_history.append(message_api)
    return message_history


# Crea la instancia de FastAPI
app = FastAPI()
db = FAISS.load_local('output/embeddings_faiss_index', OpenAIEmbeddings())

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configura el cliente de DynamoDB usando las credenciales de AWS desde las variables de entorno
session = boto3.Session(
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)

dynamodb = session.resource("dynamodb")
dynamo_table = dynamodb.Table("chatbot_v2")


# Define la ruta y función de la API para realizar preguntas
@app.post("/preguntas")
async def preguntar(mensajes: List[Message]) -> dict:
    print('mensajes in:', mensajes)
    message_history = set_messages_to_chat(mensajes)
    print('mensajes to chat:', message_history)
    message_history = await get_response_from_query(db, message_history)
    print('mensajes rta:', message_history)
    message_history = set_messages_to_api(message_history)
    print('mensajes to api:', message_history)
    # Almacena la pregunta y la respuesta en DynamoDB
    # Todo: Por alguna razón no está guardando la primer pregunta del user
    dynamo_out = save_QA_dynamodb(dynamo_table, message_history)
    print('Respuesta dynamo:', dynamo_out)
    # Todo: Consultar si es mejor que la salida sea así. Y así mismo guardarlo en dynamo
    # Pros: Mayor reproducibilidad, Contra: Más gasto de almacenamiento
    # {status: "success", "input": message_history[:-1], "output": message_history[-1]}
    return {"status": "success", "data": message_history}


# Define la función principal para ejecutar la aplicación con uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
