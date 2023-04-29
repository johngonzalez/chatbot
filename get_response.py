from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain

from dotenv import load_dotenv
load_dotenv()

def get_response_from_query(db, query):
    """
    gpt-3.5-turbo can handle up to 4097 tokens. Setting the chunksize to 1000 and k to 4 maximizes
    the number of tokens to analyze.
    """

    retriever = db.as_retriever()
    docs = retriever.get_relevant_documents(query)
    docs_page_content = " ".join([d.page_content for d in docs[:3]])

    chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    # Template to use for the system message prompt
    system_template = """
        Actúa como un asesor muy informado.

        Un usuario te realizará preguntas y debes responder utilizando la siguiente información:
        {docs}
        
        Si siente que la información anterior no es suficiente para responder la pregunta, diga "No sé".
        Sus respuestas deben ser precisas detalladas.
        """
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    # Human question prompt
    human_template = "Como asesor del banco de Bogotá, responde esta pregunta: {question}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    chain = LLMChain(llm=chat, prompt=chat_prompt)

    response = chain.run(question=query, docs=docs_page_content)
    response = response.replace("\n", "")
    return response

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
question = 'Si tengo un crédito preaprobado, cuál es el siguiente paso?, puedo autogestionarme?'
get_response_from_query(db, question)



## Todo: Manejar este error:   raise self.handle_error_response(
# openai.error.InvalidRequestError: This model's maximum context length is 4097 tokens. However, your messages resulted in 4124 tokens. Please reduce the length of the messages.



