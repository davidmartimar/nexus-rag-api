import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# Configuration
CHROMA_DB_DIR = "/app/chroma_db"
COLLECTION_NAME = "nexus_knowledge"

def get_answer(query: str):
    """
    1. Embeds the query.
    2. Searches ChromaDB for relevant chunks.
    3. Sends chunks + query to LLM.
    4. Returns answer + sources.
    """
    try:
        # 1. Initialize Vector DB Connection
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )

        # 2. Initialize LLM (The Brain)
        # temperature=0 means strict factual answers (good for technical docs)
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# 3. Create RAG Chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_db.as_retriever(search_kwargs={"k": 6}), 
            return_source_documents=True
        )

        # 4. Ask the question
        result = qa_chain({"query": query})
        
        # 5. Format Output
        answer = result["result"]
        sources = [doc.page_content for doc in result["source_documents"]]
        
        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        print(f"Error generating answer: {e}")
        raise e