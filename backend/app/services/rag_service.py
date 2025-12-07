import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# Configuration
CHROMA_DB_DIR = "/app/chroma_db"
COLLECTION_NAME = "nexus_knowledge"

def index_document(file_path: str):
    """
    1. Loads the PDF
    2. Splits into chunks
    3. Embeds and stores in ChromaDB
    """
    try:
        # 1. Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # 2. Split Text (Chunks)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        # 3. Embed & Store
        # We assume OPENAI_API_KEY is in os.environ via python-dotenv
        embeddings = OpenAIEmbeddings()
        
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_DB_DIR,
            collection_name=COLLECTION_NAME
        )
        
        vector_db.persist()
        
        return {
            "status": "success", 
            "chunks_created": len(chunks),
            "collection": COLLECTION_NAME
        }
        
    except Exception as e:
        print(f"Error indexing document: {e}")
        raise e