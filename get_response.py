from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from pydantic import BaseModel
from tiktoken import encoding_for_model

from dotenv import load_dotenv
load_dotenv()


class Message(BaseModel):
    text: str
    sender: str


def format_context(relevant_docs):
    return " ".join([d.page_content for d in relevant_docs])


def get_similar_docs(db, query, k):
    retriever = db.as_retriever()
    docs = retriever.get_relevant_documents(query)
    return docs[:k]


def get_system_message_prompt(context):

    prompt = """
        Actúa como un asesor del "banco de Bogotá".
        Responde preguntas de manera cordial, precisa, detallada y con la mayor veracidad posible
        Si tu no estás seguro de la respuesta diga "Disculpa, no sé"

        Contexto:
        {docs}
        """

    return prompt.format(docs=context)


def get_human_message_prompt(question, additional_context=None):
    partA = 'Contexto adicional: {context}'
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


def get_more_context(messages):
    # Tomamos el mensaje del sistema y último query del usuario
    system_message = messages[0].content
    latest_query = messages[-1].content

    # Revisamos cuantos tokens acumulan entre estos dos mensajes
    token_count = get_token_size(system_message + ' ' + latest_query)
    print('NUM TOKENS:', token_count)

    # Incluimos la mayor cantidad de mensajes posible si no superan 1k tokens
    new_messages = []
    for message in reversed(messages[1:-1]):
        token_count += get_token_size(message.content)
        print('NUM TOKENS:', token_count)
        if token_count > 1000:
            break
        new_messages.append(message.content)

    # Agregamos los mensajes
    query_messages = [system_message] + new_messages + [latest_query]
    query_text = '\n'.join(query_messages)

    # Agregue más contexto usando solo el último documento más importante. Todo: Si el documento ya está busque otro
    docs = get_similar_docs(db, query_text, k=1)
    # print('\n\n\nDOC\n\n\n'.join([d.page_content for d in docs]))
    more_context = format_context(docs)
    query_with_context = get_human_message_prompt(latest_query, more_context)
    return query_with_context


def get_response_from_query(db, messages):
    model_name = 'gpt-3.5-turbo'
    chat = ChatOpenAI(model_name=model_name, temperature=0, verbose=True)

    if len(messages) == 1:
        query = messages[0].content
        docs = get_similar_docs(db, query, k=3)
        # print('\n\n\nDOC\n\n\n'.join([d.page_content for d in docs]))
        context = format_context(docs)
        system_message_prompt = get_system_message_prompt(context)
        human_message_prompt = get_human_message_prompt(query)

        system_message = SystemMessage(content=system_message_prompt)
        latest_query = [HumanMessage(content=human_message_prompt)]

        response = chat([system_message] + latest_query)
        messages = [system_message] + messages

    else:
        token_limit = 4000
        lastest_query_with_context = get_more_context(messages)

        system_message = messages[0]
        num_tokens = get_token_size(
            system_message.content + ' ' + lastest_query_with_context)
        print('NUM TOKENS:', num_tokens)

        add_messages = [HumanMessage(content=lastest_query_with_context)]
        # En reversa agregue mensajes siempre y cuando no supere el límite de tokens
        for message in reversed(messages[1:-1]):
            num_tokens += get_token_size(message.content) + 4
            print('NUM TOKENS:', num_tokens)
            if num_tokens > token_limit:
                break
            add_messages = [message] + add_messages

        response = chat([system_message] + add_messages)

    return messages + [response]


db = FAISS.load_local('output/embeddings_faiss_index', OpenAIEmbeddings())
# question = 'Qué pasa si no pago mi deuda a tiempo?'
# question = 'Cuál es la estructura corporativa del banco?'
# question = 'Quiénes son sus principales ejecutivos?'
# question = 'Gano un millón de pesos, puedo acceder a una tarjeta de crédito?'
# question = 'Cuáles son los requisitos para acceder a una tarjeta de crédito si gano un millón de pesos?'
# question = 'Cuáles son los beneficios de adquirir una tarjeta débito preferente?'
# question = 'El cajero automático me ha robado, que hago?'
# question = 'El cajero automático no me dio la plata que le pedí, que hago?'
# question = 'Cuál es el número de la servilinea en Bogotá?'
# question = 'Cuál es el número de la servilinea en Soacha?'


# 1. Inicialice con el mensaje del usuario
message = Message(sender='user',
                  text='Hola. Vivo en Bogotá. Necesito retirar dinero')

# Message history trae el mensaje del sistema + usuario + rta ia (3 en total)
message_history = get_response_from_query(
    db, [HumanMessage(content=message.text)])
print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])

# 2. Continue con la convesación (entran 4 msj en total)
message = Message(sender='user',
                  text='Deseo retirar dinero en un cajero, específicamente en el Norte')

message_history.append(HumanMessage(content=message.text))

message_history = get_response_from_query(db, message_history)
print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])

# 3. Continue con la convesación (entran 5 msj en total)
message = Message(sender='user',
                  text='Me puedes dar la ubicación exacta de un cajero automático cerca a cedritos')

message_history.append(HumanMessage(content=message.text))

message_history = get_response_from_query(db, message_history)
print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])

# 4. Continue con la convesación (entran 6 msj en total)
message = Message(sender='user',
                  text='y tienes el horario de funcionamiento de algún cajero cerca?')

message_history.append(HumanMessage(content=message.text))
message_history = get_response_from_query(db, message_history)
print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])


# 5. Continue con la convesación (entran 7 msj en total)
message = Message(sender='user',
                  text='y oficinas de atención?, tienes la ubicación y horario?')

message_history.append(HumanMessage(content=message.text))
message_history = get_response_from_query(db, message_history)
print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])

# 6. Continue con la convesación (entran 8 msj en total) Error! el num dado es el 018000 912 227 (BBVA)
# message = Message(sender='user',
#                   text='Si por favor, dame el número de servicio al cliente')

message = Message(sender='user',
                  text='Este número no es del banco de bogotá')

message_history.append(HumanMessage(content=message.text))
message_history = get_response_from_query(db, message_history)
print('='*80+'\nRESPUESTA\n'+'='*80 + '\n', message_history[-1])


print('Cantidad de mensajes en total:', len(message_history))
# Todo: Manejar este error:   raise self.handle_error_response(
# openai.error.InvalidRequestError: This model's maximum context length is 4097 tokens. However, your messages resulted in 4124 tokens. Please reduce the length of the messages.
