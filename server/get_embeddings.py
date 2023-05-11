from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import BSHTMLLoader
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
load_dotenv()

def get_embeddigns():
    documents = DirectoryLoader('output/html/with_content', loader_cls=BSHTMLLoader).load()

    # documents = BSHTMLLoader('output/html/with_content/079_cobranza-prejudicial.html').load()
    text_splitter = CharacterTextSplitter(separator='\n'*7, chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    db = FAISS.from_documents(texts, OpenAIEmbeddings())
    db.save_local('output/embeddings_faiss_index')

get_embeddigns()