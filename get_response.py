from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
# from langchain.prompts.chat import (
#     ChatPromptTemplate,
#     SystemMessagePromptTemplate,
#     HumanMessagePromptTemplate,
# )

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
# from langchain.chains import LLMChain
from pydantic import BaseModel

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


def get_system_message_prompt(context, more_context=None):

    prompt = """
        Actúa como un asesor muy informado.

        Un usuario te realizará preguntas y debes responder utilizando el siguiente contexto:
        {docs}

        Si siente que la información anterior no es suficiente para responder la pregunta, diga "No sé".
        """

    return prompt.format(docs=context)


def get_human_message_prompt(question, additional_context=None):
    partA = 'Como asesor del banco de Bogotá, responde esta pregunta de manera cordial, precisa y detallada: {question}'
    partB = 'Usando este contexto adicional: {context}'
    
    if additional_context:
        prompt = (partA + '\n' + partB).format(question=question, context=additional_context)
    else:
        prompt = partA.format(question=question)
    
    return prompt


def get_response_from_query(db, messages):
    chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, verbose=True)

    if len(messages) == 1:
        query = messages[0].text
        docs = get_similar_docs(db, query, k=3)
        context = format_context(docs)
        system_message_prompt = get_system_message_prompt(context)
        human_message_prompt = get_human_message_prompt(query)

        system_message = SystemMessage(content=system_message_prompt)
        latest_query = HumanMessage(content=human_message_prompt)
        
        messages = [system_message] + [latest_query]
        response = chat(messages)
    
    else:
        system_message = messages[0]
        latest_query = messages[-1].content

        new_messages = []
        # token_count = sum([len(encoding.encode(m)) for m in keep_messages])
        # fit in as many of the previous human messages as possible
        for message in messages[1:-1]:
            # token_count += len(encoding.encode(message.text))

            # if token_count > 750:
            #     break

            new_messages.append(message.content)
            
        query_messages = [system_message.content] + new_messages + [latest_query]
        query_text = '\n'.join(query_messages)

        # Agregue más contexto usando solo el último documento más importante
        docs = get_similar_docs(db, query_text, k=1)
        more_context = format_context(docs)        
        latest_query = get_human_message_prompt(latest_query, additional_context = more_context)
        latest_query = HumanMessage(content=latest_query)

        add_messages = [latest_query]

        for message in reversed(messages[1:-1]):
            # count the number of new tokens
            # num_tokens += 4
            # num_tokens += len(encoding.encode(message.text))

            # if num_tokens > token_limit:
            #     # if we're over the token limit, stick with what we've got
            #     break
            # else:
            #     # otherwise, add the new message in after the system prompt, but before the rest of the messages we've added
            #     new_message = HumanMessage(content=message.text) if message.sender == 'user' else AIMessage(content=message.text)
            #     messages = [new_message] + messages
            new_message = HumanMessage(content=message.content) if isinstance(message, HumanMessage) else AIMessage(content=message.content)
            add_messages = [new_message] + add_messages

        response = chat(add_messages)
        
    return messages, response

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

message = Message(sender='user',
                  text='Hola. Vivo en Bogotá. Necesito retirar dinero')

# Inicialice
message_history, ai_message = get_response_from_query(db, [message])
print('='*80+'\nRESPUESTA\n'+'='*80 +'\n', ai_message)
messages = message_history
messages.append(ai_message)


# Continue con la convesación
message = Message(sender='user',
                  text='Específicamente en el Norte')


messages.append(HumanMessage(content=message.text))

message_history, ai_message = get_response_from_query(db, messages)
print('='*80+'\nRESPUESTA\n'+'='*80 +'\n', ai_message)


# Continue con la convesación
message = Message(sender='user',
                  text='Me puedes dar ubicaciones?')


messages.append(HumanMessage(content=message.text))

message_history, ai_message = get_response_from_query(db, messages)
print('='*80+'\nRESPUESTA\n'+'='*80 +'\n', ai_message)


# Continue con la convesación
message = Message(sender='user',
                  text='Me las puedes listar 10 con su horario de atención')


messages.append(HumanMessage(content=message.text))

message_history, ai_message = get_response_from_query(db, messages)
print('='*80+'\nRESPUESTA\n'+'='*80 +'\n', ai_message)


## Todo: Manejar este error:   raise self.handle_error_response(
# openai.error.InvalidRequestError: This model's maximum context length is 4097 tokens. However, your messages resulted in 4124 tokens. Please reduce the length of the messages.



