from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

from pydantic import BaseModel
from tiktoken import encoding_for_model

from uuid import uuid4
from datetime import datetime as dt

from dotenv import load_dotenv
load_dotenv()


class Message(BaseModel):
    text: str
    sender: str


def format_context(relevant_docs):
    # print(relevant_docs)
    return {
        'text': ' '.join([d.page_content for d in relevant_docs]),
        # 'sources': [d.metadata['source'] for d in relevant_docs]
    }


def get_similar_docs(db, query, k):
    retriever = db.as_retriever()
    docs = retriever.get_relevant_documents(query)
    return docs[:k]


def get_system_message_prompt(context):
    # print(context)

    prompt = """Tu nombre es Linguo. Actúas como un asesor de "seguros adl".
Tu función es responder preguntas e inquitudes acerca del paquete de beneficios de los colaboradores de la empresa.
Muestra disponibilidad y cordialidad al responder, debes ser preciso.
Utiliza de acuerdo a la información del "Contexto" que te suministrará el usuario.
Si el contexto no es suficiente, responde 'Disculpa, no tengo respuesta a tu pregunta, dirígete a maria.forero@avaldigitallabs.com en el canal de slack'"""
    return prompt.format(docs=context)


def get_human_message_prompt(question, additional_context=None):
    # print('='*80, 'additional_context:', additional_context)
    partA = '"Contexto": {context}'
    partB = 'Pregunta: {question}'

    if additional_context:
        prompt = (partA + '\n' + partB).format(context=additional_context,
                                               question=question)
    else:
        prompt = partB.format(question=question)

    return prompt


def get_token_size(message, model_name='gpt-3.5-turbo'):
    encoding = encoding_for_model(model_name)
    return len(encoding.encode(message))


def get_more_context(db, chat, messages):
    # Tomamos el mensaje del sistema y último query del usuario
    system_message = messages[0].content
    latest_query = messages[-1].content

    # Revisamos cuantos tokens acumulan entre estos dos mensajes
    # token_count = get_token_size(system_message + ' ' + latest_query)
    token_count = chat.get_num_tokens_from_messages(
        [messages[0], messages[-1]])

    # Incluimos la mayor cantidad de mensajes posible si no superan 1k tokens
    new_messages = []

    # Todo: Debería conseguir el contexto solo de las preguntas realizadas por el user
    # Porque el user es el que muestra la intención, la ia podría sesgar esta intención
    for message in reversed(messages[1:-1:2]):
        token_count += chat.get_num_tokens(message.content) + 4
        if token_count > 750:
            break
        new_messages.append(message.content)

    # Agregamos los mensajes
    # query_messages = [system_message] + new_messages + [latest_query]
    query_messages = new_messages + [latest_query]
    query_text = '\n'.join(query_messages)

    # Agregue más contexto usando solo el último documento más importante. Todo: Si el documento ya está busque otro
    docs = get_similar_docs(db, query_text, k=3)
    # print('\n\n\nDOC\n\n\n'.join([d.page_content for d in docs]))
    context = format_context(docs)
    print(context)
    more_context = context['text']

    # print('NUM TOKENS:', chat.get_num_tokens(get_human_message_prompt(latest_query, more_context)))
    return {
        'query_with_context': get_human_message_prompt(latest_query, more_context),
        # 'sources': context['sources']
    }


async def get_response_from_query(db, messages):
    model_name = 'gpt-3.5-turbo'
    chat = ChatOpenAI(model_name=model_name, temperature=0, verbose=True)
    def get_dt(): return dt.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    default_session_id = uuid4()
    token_limit = 4000

    # Inicializa conversación
    if len(messages) == 1:
        query = messages[0].content
        docs = get_similar_docs(db, query, k=3)
        # print('\n\n\nDOC\n\n\n'.join([d.page_content for d in docs]))
        context = format_context(docs)
        # sources = context['sources']  # Todo: Pensar como exportar estas fuentes. En los mensajes?
        # system_message_prompt = get_system_message_prompt(context['text'])
        system_message_prompt = get_system_message_prompt(None)
        human_message_prompt = get_human_message_prompt(query, additional_context=context['text'])

        additional_kwargs = messages[0].additional_kwargs
        additional_kwargs = {
            'id': additional_kwargs.get('id', uuid4()),
            'datetime': additional_kwargs.get('datetime', get_dt()),
            'session_id': additional_kwargs.get('session_id', default_session_id)
        }
        last_message = [HumanMessage(
            content=human_message_prompt,
            additional_kwargs=additional_kwargs
        )]

        message_user = [HumanMessage(
            content=query,
            additional_kwargs=additional_kwargs
        )]
        # ojo! se debe crear una copia del diccionario
        additional_kwargs_system = dict(additional_kwargs)
        additional_kwargs_system['id'] = uuid4()
        system_message = SystemMessage(
            content=system_message_prompt,
            additional_kwargs=additional_kwargs_system
        )
        messages = [system_message] + message_user # last_message

    # Continúa conversación
    else:
        context = get_more_context(db, chat, messages)
        system_message = messages[0]
        last_query = context['query_with_context']

        # Conseguir el contexto puede desbordar los tokens; se comprueba primero
        # Todo: Aún así se debe comprobar que la misma pregunta no lo desborde
        if chat.get_num_tokens(system_message.content + ' ' + last_query) + 8 > token_limit:
            print('Warning: No agrega contexto último mensaje, desborda límite tokens')
            last_query = get_human_message_prompt(messages[-1].content)

        last_message = [HumanMessage(content=last_query)]

        num_tokens = chat.get_num_tokens_from_messages(
            [system_message, last_message[0]])

        # En reversa agregue mensajes del user siempre y cuando no supere el límite de tokens
        for message in reversed(messages[1:-1]):
            # todo: Sumar los tokens del rol: system, user, assistant. Contribuyen muy poco
            num_tokens += chat.get_num_tokens(message.content) + 4
            # print('NUM TOKENS:', num_tokens)
            if num_tokens > token_limit:
                break
            last_message = [message] + last_message

        # Todo: Solo se llena la info del último msj. Pero es posible que
        # desde el llamado a la api se tenga información sin estos campos
        # en algunos mensajes. Para lo cual tendría que hacerse algunas
        # validaciones primero como que session_id sea el mismo, que exista
        # un system message en el mensaje cero. Que el orden de los mensajes
        # sea coherente con datetime sino ordenarlos.
        messages[-1].additional_kwargs = {
            'id': messages[-1].additional_kwargs.get('id', uuid4()),
            'datetime': messages[-1].additional_kwargs.get('id', get_dt()),
            'session_id': messages[0].additional_kwargs.get('session_id', default_session_id),
        }

    q = [system_message] + last_message
    tokens_query = chat.get_num_tokens_from_messages(q)
    if tokens_query > token_limit:
        print(f'Error: El número de tokens supera el límite {token_limit}')
        # TODO: Enviar esto como salida de error con su mensaje
        raise

    response = chat(q)
    response.additional_kwargs = {
        'id': uuid4(),
        'datetime': get_dt(),
        'session_id': messages[0].additional_kwargs.get('session_id', default_session_id),
        'tokens_query': tokens_query,
        'tokens_respo': chat.get_num_tokens_from_messages([response]),
    }
    return messages + [response]

# import sys
# base_path = '/home/john/Proyectos/chatbot/chatbot_beneficios/server'
# sys.path.append(base_path)
# db = FAISS.load_local(base_path + '/output/embeddings_faiss_index', OpenAIEmbeddings())

# # 1. Inicialice con el mensaje del usuario
# message = Message(sender='user',
#                   text='Hola')

# # Message history trae el mensaje del sistema + usuario + rta ia (3 en total)
# message_history = get_response_from_query(
#     db, [HumanMessage(content=message.text)])
# print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])

# # 2. Continue con la convesación (entran 4 msj en total)
# message = Message(sender='user',
#                   text='actualmente tengo el ahorro de vacaciones con porvenir. Quisiera saber si puedo realizar retiros totales o parciales en cualquier momento y no solo cuando pida dias de vacaciones.')

# message_history.append(HumanMessage(content=message.text))

# message_history = get_response_from_query(db, message_history)
# print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])


# # 3. Continue con la convesación (entran 5 msj en total)
# message = Message(sender='user',
#                   text='')

# message_history.append(HumanMessage(content=message.text))

# message_history = get_response_from_query(db, message_history)
# print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])

# # 4. Continue con la convesación (entran 6 msj en total)
# message = Message(sender='user',
#                   text='y tienes el horario de funcionamiento de algún cajero cerca?')

# message_history.append(HumanMessage(content=message.text))
# message_history = get_response_from_query(db, message_history)
# print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])


# # 5. Continue con la convesación (entran 7 msj en total)
# message = Message(sender='user',
#                   text='vivo cerca al barrio cedritos')

# message_history.append(HumanMessage(content=message.text))
# message_history = get_response_from_query(db, message_history)
# print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])

# # 6. Continue con la convesación (entran 8 msj en total) Error! el num dado es el 018000 912 227 (BBVA) o 01 8000 912345 (Bancolombia)
# message = Message(sender='user',
#                   text='Perdón tienes el número de servicio al cliente')

# # message = Message(sender='user',
# #                   text='Me das la fuente de donde obtuviste este número de teléfono?')

# message_history.append(HumanMessage(content=message.text))
# message_history = get_response_from_query(db, message_history)
# print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])


# print('Cantidad de mensajes en total:', len(message_history))
# # Todo: Manejar este error:   raise self.handle_error_response(
# # openai.error.InvalidRequestError: This model's maximum context length is 4097 tokens. However, your messages resulted in 4124 tokens. Please reduce the length of the messages.
