import os
import shutil
import zipfile
import json
import uuid
import openai
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# Configuration
CHROMA_DB_DIR = "/app/chroma_db"
DEFAULT_COLLECTION_NAME = "nexus_slot_1"

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio using OpenAI Whisper API.
    """
    try:
        client = openai.OpenAI()
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        raise e

def load_document(file_path: str):
    """
    Selects the appropriate loader based on file extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        loader = PyMuPDFLoader(file_path)
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

def index_document(file_path: str, collection_name: str = DEFAULT_COLLECTION_NAME):
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
            collection_name=collection_name
        )
        
        vector_db.persist()
        
        return {
            "status": "success", 
            "chunks_created": len(chunks),
            "collection": collection_name
        }
        
    except Exception as e:
        print(f"Error indexing document: {e}")
        raise e

def get_document_count(collection_name: str = DEFAULT_COLLECTION_NAME):
    """
    Returns the number of documents in the ChromaDB collection.
    """
    try:
        # We want to count UNIQUE documents (files), not chunks
        return len(get_all_documents(collection_name))
    except Exception:
        return 0

def get_all_documents(collection_name: str = DEFAULT_COLLECTION_NAME):
    """
    Returns a list of all unique documents currently indexed.
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR, 
            embedding_function=embeddings,
            collection_name=collection_name
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

def delete_document(filename: str, collection_name: str = DEFAULT_COLLECTION_NAME):
    """
    Deletes a document from the vector store and the filesystem.
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR, 
            embedding_function=embeddings,
            collection_name=collection_name
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

def reset_knowledge_base(collection_name: str = DEFAULT_COLLECTION_NAME):
    """
    Deletes the specific collection.
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        # Delete using the public API if possible, or correct private usage
        # vector_db.delete_collection() completely removes it. 
        # But we want to keep the slot, just empty it.
        # So we delete all where "source" exists (which is all our docs)
        
        # Method 1: Delete Collection
        try:
             vector_db.delete_collection()
        except:
             pass 
             
        # Re-init to ensure it exists empty
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        vector_db.persist()
        
        # Also clear the uploaded files for this slot?
        # Our uploads are in a flat dir /app/data_uploads. We should clean them.
        # But wait, data_uploads isn't separated by slot.
        # If we delete "CV.pdf" from slot 1, but it was also used in slot 2?
        # Current implementation shares /app/data_uploads.
        # Ideally we don't delete files from disk if they might be used elsewhere.
        # But the user expects "Erase All" to wipe data.
        # For now, let's just wipe the Vector DB content.
        
        return True
    except Exception as e:
        print(f"Error reseting knowledge base: {e}")
        return False

def create_backup():
    """
    Zips the chroma_db directory.
    """
    try:
        backup_path = "/app/backup.zip"
        # shutil.make_archive defaults to zip if format is 'zip'
        # root_dir is parent of base_dir.
        # We want to zip CHROMA_DB_DIR.
        shutil.make_archive("/app/backup", 'zip', CHROMA_DB_DIR)
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        raise e

def export_slot_data(collection_name: str) -> str:
    """
    Exports the vectors and source files of a specific slot to a zip.
    """
    try:
        export_dir = f"/app/export_{collection_name}_{uuid.uuid4().hex[:8]}"
        os.makedirs(export_dir, exist_ok=True)
        
        # 1. Fetch Data from Chroma
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Get all data including embeddings to avoid re-calculating cost
        data = vector_db._collection.get(include=['embeddings', 'metadatas', 'documents'])
        
        # 2. Save Vectors
        vectors_path = os.path.join(export_dir, "vectors.json")
        with open(vectors_path, "w") as f:
            json.dump(data, f)
            
        # 3. Collect Source Files
        files_dir = os.path.join(export_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        if data['metadatas']:
            for meta in data['metadatas']:
                if meta and "source" in meta:
                    # We expect source to be /app/data_uploads/filename
                    filename = os.path.basename(meta["source"])
                    src_path = f"/app/data_uploads/{filename}"
                    dst_path = os.path.join(files_dir, filename)
                    if os.path.exists(src_path) and not os.path.exists(dst_path):
                        shutil.copy2(src_path, dst_path)
                        
        # 4. Zip
        zip_path = f"/app/export_{collection_name}.zip"
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', export_dir)
        
        # Cleanup temp
        shutil.rmtree(export_dir)
        
        return zip_path
    except Exception as e:
        print(f"Error exporting slot: {e}")
        return None

def import_slot_data(collection_name: str, zip_path: str):
    """
    Imports vectors and files into the specified slot.
    """
    try:
        temp_dir = f"/app/import_temp_{uuid.uuid4().hex[:8]}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 1. Unzip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # 2. Load Vectors
        vectors_path = os.path.join(temp_dir, "vectors.json")
        if not os.path.exists(vectors_path):
            raise ValueError("Invalid backup: vectors.json missing")
            
        with open(vectors_path, "r") as f:
            data = json.load(f)
            
        # 3. Copy Files
        files_dir = os.path.join(temp_dir, "files")
        if os.path.exists(files_dir):
            for filename in os.listdir(files_dir):
                shutil.copy2(os.path.join(files_dir, filename), os.path.join("/app/data_uploads", filename))
                
        # 4. Inject into Chroma
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Upsert (Add or Update)
        # Chroma expects lists
        if data['ids']:
            vector_db._collection.upsert(
                ids=data['ids'],
                embeddings=data['embeddings'],
                metadatas=data['metadatas'],
                documents=data['documents']
            )
            # Persist if needed (older chroma versions), newer autosaves
            vector_db.persist()
            
        # Cleanup
        shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        print(f"Error importing slot: {e}")
        return False
        
def get_slot_config():
    config_path = os.path.join(CHROMA_DB_DIR, "slots.json")
    default_config = {
        "nexus_slot_1": "Memory Slot 1"
    }
    
    if not os.path.exists(config_path):
        print(f"DEBUG: Config file not found at {config_path}. Using default.")
        return default_config
        
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            print(f"DEBUG: Loaded config from {config_path}: {data}")
            return data
    except Exception as e:
        print(f"DEBUG: Error loading config from {config_path}: {e}")
        return default_config

def save_slot_config(config: dict):
    # Ensure dir exists (it should if app is running)
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    config_path = os.path.join(CHROMA_DB_DIR, "slots.json")
    try:
        print(f"DEBUG: Saving config to {config_path}: {config}")
        with open(config_path, "w") as f:
            json.dump(config, f)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def create_slot(name: str):
    config = get_slot_config()
    slot_id = f"nexus_slot_{uuid.uuid4().hex[:8]}"
    config[slot_id] = name
    if save_slot_config(config):
        return slot_id
    return None

def delete_slot(slot_id: str):
    config = get_slot_config()
    if slot_id in config:
        # 1. Delete the actual data
        reset_knowledge_base(slot_id)
        # 2. Remove from config
        del config[slot_id]
        return save_slot_config(config)
    return False

