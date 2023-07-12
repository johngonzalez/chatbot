from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
load_dotenv()


def get_embeddigns(doc_path: str, emb_path: str) -> None:
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
    )
    with open(doc_path) as f:
        doc_app_beneficios = f.read()

    docs_app_beneficios = markdown_splitter.split_text(doc_app_beneficios)
    print('Cantidad documentos:', len(docs_app_beneficios))
    db = FAISS.from_documents(docs_app_beneficios, OpenAIEmbeddings())
    db.save_local(emb_path)
    print('Embeddings fueron almacenados en:', emb_path)

get_embeddigns('data/app_beneficios.md', 'output/embeddings_faiss_index')