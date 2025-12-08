import os
import openai
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document

# Configuration
CHROMA_DB_DIR = "/app/chroma_db"
COLLECTION_NAME = "nexus_knowledge"

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio using OpenAI Whisper API.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript["text"]
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        raise e

def load_document(file_path: str):
    """
    Selects the appropriate loader based on file extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        return loader.load()
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
        return loader.load()
    elif ext in [".txt", ".md"]:
        loader = TextLoader(file_path)
        return loader.load()
    elif ext in [".mp3", ".wav", ".m4a", ".mp4"]:
        # Audio handling: Transcribe then wrap in Document
        text = transcribe_audio(file_path)
        return [Document(page_content=text, metadata={"source": file_path})]
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def index_document(file_path: str):
    """
    1. Loads the file (PDF, DOCX, TXT, MD, Audio)
    2. Splits into chunks
    3. Embeds and stores in ChromaDB
    """
    try:
        # 1. Load Document
        documents = load_document(file_path)
        
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

def get_document_count():
    """
    Returns the number of documents in the ChromaDB collection.
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR, 
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
        return vector_db._collection.count()
    except Exception:
        return 0

def get_all_documents():
    """
    Returns a list of all unique documents currently indexed.
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR, 
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
        
        # Get all metadata to find unique sources
        collection_data = vector_db._collection.get(include=["metadatas"])
        metadatas = collection_data.get("metadatas", [])
        
        unique_files = set()
        for meta in metadatas:
            if meta and "source" in meta:
                # Extract filename from the source path
                filename = os.path.basename(meta["source"])
                unique_files.add(filename)
                
        return list(unique_files)
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return []

def delete_document(filename: str):
    """
    Deletes a document from the vector store and the filesystem.
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR, 
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
        
        # Reconstruct potential source path (best effort)
        # We know ingest saves to /app/data_uploads/{filename}
        # But we need to be careful to match how it was stored.
        # Ideally, we query by metadata where source ends with filename.
        
        collection_data = vector_db._collection.get(where={"source": {"$ne": ""}}, include=["metadatas"])
        ids_to_delete = []
        
        # Find IDs associated with this filename
        # Note: Chroma's `where` filter is basic, so we might need to iterate if we can't efficiently filter by substring
        # Actually, we can just delete by the exact source path we expect.
        target_source_path = f"/app/data_uploads/{filename}"
        
        # However, to be robust, let's find all chunks that have this filename in their source path
        # Currently we just use the exact path we controlled in ingest.py
        
        vector_db._collection.delete(where={"source": target_source_path})
        vector_db.persist()
        
        # Now delete the actual file
        file_path = os.path.join("/app/data_uploads", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return True
    except Exception as e:
        print(f"Error deleting document {filename}: {e}")
        return False
