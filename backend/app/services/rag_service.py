import os
import shutil
import zipfile
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import openai
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# Load environment variables (ensure OPENAI_API_KEY is present)
load_dotenv()

logger = logging.getLogger(__name__)

# Constants and Configuration
CHROMA_DB_DIR = Path("/app/chroma_db")
UPLOAD_DIR = Path("/app/data_uploads")
DEFAULT_COLLECTION_NAME = "nexus_slot_1"


def transcribe_audio(file_path: str) -> str:
    """Transcribes audio using OpenAI Whisper API."""
    try:
        client = openai.OpenAI()
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        logger.error(f"Error transcribing audio {file_path}: {e}", exc_info=True)
        raise


def load_document(file_path: str) -> List[Document]:
    """Selects the appropriate loader based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
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
            text = transcribe_audio(file_path)
            return [Document(page_content=text, metadata={"source": file_path})]
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        logger.error(f"Failed to load document {file_path}: {e}", exc_info=True)
        raise


def index_document(file_path: str, collection_name: str = DEFAULT_COLLECTION_NAME) -> Dict[str, Any]:
    """
    Ingestion Pipeline:
    1. Loads the file.
    2. Splits text into semantic chunks.
    3. Embeds and stores chunks in ChromaDB.
    """
    try:
        documents = load_document(file_path)
        
        # Semantic chunking strategy
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(CHROMA_DB_DIR),
            collection_name=collection_name
        )
        
        # Note: vector_db.persist() is deprecated in newer Chroma versions as it autosaves,
        # but kept here for backward compatibility with older langchain-chroma wrappers.
        vector_db.persist()
        
        logger.info(f"Successfully indexed {len(chunks)} chunks into {collection_name}")
        return {
            "status": "success", 
            "chunks_created": len(chunks),
            "collection": collection_name
        }
        
    except Exception as e:
        logger.error(f"Error indexing document {file_path}: {e}", exc_info=True)
        raise


def get_all_documents(collection_name: str = DEFAULT_COLLECTION_NAME) -> List[str]:
    """Returns a list of all unique documents currently indexed in the specified slot."""
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=str(CHROMA_DB_DIR), 
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Accessing the underlying chromadb client collection directly to fetch metadata
        # because LangChain's high-level wrapper abstracts away bulk metadata retrieval.
        collection_data = vector_db._collection.get(include=["metadatas"])
        metadatas = collection_data.get("metadatas", [])
        
        unique_files = set()
        for meta in metadatas:
            if meta and "source" in meta:
                filename = os.path.basename(meta["source"])
                unique_files.add(filename)
                
        return list(unique_files)
    except Exception as e:
        logger.error(f"Error fetching documents for {collection_name}: {e}", exc_info=True)
        return []


def get_document_count(collection_name: str = DEFAULT_COLLECTION_NAME) -> int:
    """Returns the number of unique documents in the ChromaDB collection."""
    try:
        return len(get_all_documents(collection_name))
    except Exception as e:
        logger.error(f"Error counting documents for {collection_name}: {e}")
        return 0


def delete_document(filename: str, collection_name: str = DEFAULT_COLLECTION_NAME) -> bool:
    """Deletes a document's vectors from the store and removes the source file."""
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=str(CHROMA_DB_DIR), 
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        target_source_path = str(UPLOAD_DIR / filename)
        
        # Direct access to the Chroma client to perform deletion by metadata filter.
        vector_db._collection.delete(where={"source": target_source_path})
        vector_db.persist()
        
        # Remove original file from disk if it exists
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            file_path.unlink()
            
        logger.info(f"Successfully deleted {filename} from {collection_name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting document {filename}: {e}", exc_info=True)
        return False


def reset_knowledge_base(collection_name: str = DEFAULT_COLLECTION_NAME) -> bool:
    """Deletes all vectors in a specific collection, effectively emptying the slot."""
    try:
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=str(CHROMA_DB_DIR),
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        try:
             vector_db.delete_collection()
        except Exception as delete_error:
             logger.warning(f"Could not delete collection natively, it may be empty. Error: {delete_error}")
             
        # Re-initialize empty collection
        vector_db = Chroma(
            persist_directory=str(CHROMA_DB_DIR),
            embedding_function=embeddings,
            collection_name=collection_name
        )
        vector_db.persist()
        
        logger.info(f"Knowledge base '{collection_name}' has been successfully reset.")
        return True
    except Exception as e:
        logger.error(f"Critical error resetting knowledge base {collection_name}: {e}", exc_info=True)
        return False


def export_slot_data(collection_name: str) -> Optional[str]:
    """Exports the vectors and source files of a specific slot to a zip archive."""
    export_dir = Path(f"/app/export_{collection_name}_{uuid.uuid4().hex[:8]}")
    zip_path_str = f"/app/export_{collection_name}.zip"
    
    try:
        export_dir.mkdir(parents=True, exist_ok=True)
        
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=str(CHROMA_DB_DIR),
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Access private collection to retrieve full raw embeddings and metadata
        data = vector_db._collection.get(include=['embeddings', 'metadatas', 'documents'])
        
        vectors_path = export_dir / "vectors.json"
        with vectors_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)
            
        files_dir = export_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        
        if data.get('metadatas'):
            for meta in data['metadatas']:
                if meta and "source" in meta:
                    filename = os.path.basename(meta["source"])
                    src_path = UPLOAD_DIR / filename
                    dst_path = files_dir / filename
                    
                    if src_path.exists() and not dst_path.exists():
                        shutil.copy2(src_path, dst_path)
                        
        # Create archive (shutil automatically appends .zip)
        archive_base = zip_path_str.replace(".zip", "")
        shutil.make_archive(archive_base, 'zip', export_dir)
        
        return zip_path_str
        
    except Exception as e:
        logger.error(f"Error exporting slot {collection_name}: {e}", exc_info=True)
        return None
    finally:
        # Guarantee cleanup of temporary export directory
        if export_dir.exists():
            shutil.rmtree(export_dir, ignore_errors=True)


def import_slot_data(collection_name: str, zip_path: str) -> bool:
    """Imports vectors and source files from an archive into the specified slot."""
    temp_dir = Path(f"/app/import_temp_{uuid.uuid4().hex[:8]}")
    
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        vectors_path = temp_dir / "vectors.json"
        if not vectors_path.exists():
            raise ValueError("Invalid backup structure: vectors.json is missing.")
            
        with vectors_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        files_dir = temp_dir / "files"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        if files_dir.exists():
            for file_item in files_dir.iterdir():
                if file_item.is_file():
                    shutil.copy2(file_item, UPLOAD_DIR / file_item.name)
                    
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=str(CHROMA_DB_DIR),
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Upsert allows injecting external IDs and Embeddings directly
        if data.get('ids'):
            vector_db._collection.upsert(
                ids=data['ids'],
                embeddings=data['embeddings'],
                metadatas=data['metadatas'],
                documents=data['documents']
            )
            vector_db.persist()
            
        logger.info(f"Successfully imported data into {collection_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error importing slot data: {e}", exc_info=True)
        return False
    finally:
        # Guarantee cleanup of temporary extraction directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def get_slot_config() -> Dict[str, str]:
    """Retrieves the slot configuration file."""
    config_path = CHROMA_DB_DIR / "slots.json"
    default_config = {"nexus_slot_1": "Memory Slot 1"}
    
    if not config_path.exists():
        logger.info("Config file not found. Generating default configuration.")
        return default_config
        
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading slot config: {e}. Falling back to default.", exc_info=True)
        return default_config


def save_slot_config(config: Dict[str, str]) -> bool:
    """Saves the slot configuration to disk."""
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    config_path = CHROMA_DB_DIR / "slots.json"
    
    try:
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving slot config: {e}", exc_info=True)
        return False


def create_slot(name: str) -> Optional[str]:
    """Registers a new slot in the configuration."""
    config = get_slot_config()
    slot_id = f"nexus_slot_{uuid.uuid4().hex[:8]}"
    config[slot_id] = name
    
    if save_slot_config(config):
        logger.info(f"Created new memory slot: {slot_id}")
        return slot_id
    return None


def delete_slot(slot_id: str) -> bool:
    """Removes a slot's data and unregisters it from the configuration."""
    config = get_slot_config()
    if slot_id in config:
        reset_knowledge_base(slot_id)
        del config[slot_id]
        logger.info(f"Deleted memory slot: {slot_id}")
        return save_slot_config(config)
    
    logger.warning(f"Attempted to delete non-existent slot: {slot_id}")
    return False