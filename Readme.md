# Chatbot app de beneficios

* Forked from [chatbot johngonzalez](https://github.com/johngonzalez/chatbot.git)
* Inspired from [chat-twitter](https://github.com/mtenenholtz/chat-twitter)

## Chatea con la app de beneficios

Realiza preguntas acerca de tus beneficios. La app está públicamente hospedada [aquí]()

## Arquitectura básica
La app utiliza NextJS, Tailwind CSS como frontend. El frontend es hospedado en Vercel y el backend en un pequeño hilo en codesandbox. El backend utiliza una base de datos vectorial almacenada localmente para los emebeddings y un archivo Docker con todas las dependencias. Además las interacciones con los usuarios quedan almacenadas en una base de datos DynamoDB en la capa gratuita de AWS.

## Corriendo localmente
1. Clone el repo

```
git clone hhttps://github.com/johngonzalez/chatbot
cd chatbot
```

2. Configura tus credenciales en un archivo `.env` en la carpeta raiz. La primer credencial te da acceso a la api de openai y las demás acceso a la base de datos dynamodb:

```
OPENAI_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=...
```

5. Cree una carpeta y copie los documentos que el chat utilizará como fuente de verdad:

```
cd backend
mkdir data
cp <archivo.md> data
```

6. Instale las dependencias de python

```
# Estando en la carpeta backend
pip install -r requirements.txt
```

7.  Prepare los documentos y cree los embeddings:

```
# in the backend/ directory
mkdir output
python get_embeddings.py
```

8. Corra el servidor backend

```
# in the backend/ directory
uvicorn main:app --reload
```

3. En la carpeta raiz. Instala las dependencias node.

```
cd ..
npm i
```

4. Corre el servidor node

```
npm run dev
```


9. Listo! ya puedes iniciar a chatear
