from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
from typing import List
load_dotenv()


def get_embeddigns(doc_paths: List[str], emb_path: str) -> None:
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
    ) 

    docs = sum([
        markdown_splitter.split_text(open(doc).read())
        for doc in doc_paths
    ], [])

    print('Cantidad documentos:', len(docs))
    db = FAISS.from_documents(docs, OpenAIEmbeddings())
    db.save_local(emb_path)
    print('Embeddings fueron almacenados en:', emb_path)


# Asegúrese que estos documentos estén en la dirección indicada
doc_paths = [
    'data/info_general.md',
    # 'data/comparativo_sura.md',
    'data/comparativo_salud.md',
    'data/preguntas_respuestas.md',
    'data/vida_alfa.md',
    'data/salud_sura_global.md',
    'data/salud_sura_clasico.md',
    'data/dental_colsanitas.md',
    'data/complementario_compensar.md',
    'data/prepagada_colsanitas.md',
    'data/prepagada_vetplus.md',
    'data/prepagada_colmedica.md',
    'data/prepagada_medisanitas.md',
    'data/emermedica.md',
    'data/exequial_mapfre.md',
    'data/mascotas_alfa.md',
]

get_embeddigns(doc_paths, 'output/embeddings_faiss_index')