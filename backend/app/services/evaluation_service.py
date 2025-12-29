import os
import openai
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.testset import TestsetGenerator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain.docstore.document import Document
from app.services.rag_service import get_all_documents, CHROMA_DB_DIR
from app.services.chat_service import get_answer

# RAGAS requires OPENAI_API_KEY to be in the environment.
# It should already be set by docker-compose or .env.
if not os.getenv("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY not found in environment")

def load_all_local_documents():
    """
    Loads all documents from the data_uploads directory directly.
    We need raw documents for testset generation.
    """
    # In rag_service, we know where files are: /app/data_uploads
    # But files in docker are mapped. Here we should check where 'data_uploads' is.
    # rag_service references /app/data_uploads.
    # Note: In development on Windows, this might be a mapped path.
    # But since we are running inside the container (conceptually) or local python?
    # The user path is c:\Users\Usuario\nexus-rag-api\backend...
    # We should look at where the files ARE.
    # rag_service.py says: /app/data_uploads
    # But locally?
    # Let's trust that we can access them if we are running in the same env.
    # If running locally without docker, we might fail if /app doesn't exist.
    # We'll try to use relative path if /app not found.
    
    base_path = "/app/data_uploads"
    if not os.path.exists(base_path):
        # Fallback for local dev
        base_path = "data_uploads"
        if not os.path.exists(base_path):
            # Try relative to backend root
            base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_uploads")
    
    documents = []
    if not os.path.exists(base_path):
         print(f"Warning: Data directory {base_path} not found.")
         return []
         
    for filename in os.listdir(base_path):
        file_path = os.path.join(base_path, filename)
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".pdf":
                loader = PyMuPDFLoader(file_path)
                documents.extend(loader.load())
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
            elif ext in [".txt", ".md"]:
                loader = TextLoader(file_path)
                documents.extend(loader.load())
        except Exception as e:
            print(f"Error loading {filename} for evaluation: {e}")
            
    return documents

def generate_evaluation_testset(limit: int = 15):
    """
    Generates a synthetic testset using RAGAS.
    """
    documents = load_all_local_documents()
    if not documents:
        raise ValueError("No documents found to generate testset.")
        
    # Initialize Generator - Ragas 0.0.22
    # We use from_default() which picks up OPENAI_API_KEY and uses default models (usually gpt-3.5)
    generator = TestsetGenerator.from_default()
    
    # Generate
    # In 0.0.22, generate() accepts LangChain docs directly
    testset = generator.generate(
        documents,
        test_size=limit
    )
    
    return testset.to_pandas().to_dict(orient="records")

def run_evaluation(testset_data: list):
    """
    Runs the RAG pipeline on the testset and evaluates results.
    testset_data: List of dicts with 'question', 'ground_truth', etc.
    """
    
    results = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truths": []
    }
    
    # 1. Run RAG for each question
    for item in testset_data:
        # In 0.0.22, generator uses 'question', 'ground_truth' (singular)
        # But metrics often expect 'ground_truths' (plural, list of strings)
        q = item.get("question")
        gt = item.get("ground_truth")
        
        # Fallback if keys are different (just in case)
        if not q:
            # Try finding 'user_input' or similar if question is missing, though we verified it exists
            print(f"Skipping item with missing question: {item.keys()}")
            continue
            
        # Call into our actual system
        response = get_answer(q)
        
        results["question"].append(q)
        results["answer"].append(response["answer"])
        results["contexts"].append(response["sources"])
        # Wrap gt in list -> ground_truths is list of lists of strings
        if isinstance(gt, str):
            results["ground_truths"].append([gt])
        else:
            results["ground_truths"].append(gt)
        
    # 2. Evaluate using RAGAS
    dataset = Dataset.from_dict(results)
    
    scores = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ]
    )
    
    # Ragas Result object causes serialization issues in FastAPI
    # We convert it to a simple dict of floats
    final_scores = {}
    try:
        # Check if it behaves like a dict
        for k, v in scores.items():
            final_scores[str(k)] = float(v)
    except Exception as e:
        print(f"Error converting scores to dict: {e}")
        # Fallback: stringify
        return {"raw_scores": str(scores)}
        
    return final_scores
