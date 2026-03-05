import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables (OPENAI_API_KEY)
load_dotenv()

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
from app.schemas import UniversalLead
from app.services.rag_service import DEFAULT_COLLECTION_NAME

# Configuration
CHROMA_DB_DIR = "/app/chroma_db"
logger = logging.getLogger(__name__)


def get_answer(
    query: str, 
    collection_name: str = DEFAULT_COLLECTION_NAME, 
    history: Optional[List[Dict[str, str]]] = None, 
    business_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Core RAG Pipeline:
    1. Connects to ChromaDB for semantic search.
    2. Hydrates conversation history into LangChain Memory.
    3. Retrieves context and generates an answer via LLM.
    4. Runs a parallel structured output chain for Lead Extraction.
    """
    if history is None:
        history = []

    try:
        # 1. Initialize Vector DB Connection
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )

        # 2. Initialize LLM (Centralized for reuse)
        # gpt-3.5-turbo for testing, gpt-4o-mini for better cost/performance in production
        llm_chat = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
        
        # 3. Initialize Conversation Memory
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", 
            return_messages=True, 
            k=5,
            output_key="answer"
        )
        
        # Reconstruct Memory state from stateless API payload
        for exchange in history:
            user_msg = exchange.get("user")
            ast_msg = exchange.get("assistant")
            if user_msg and ast_msg:
                memory.save_context(
                    {"input": user_msg}, 
                    {"answer": ast_msg}
                )

        # 4. RAG Chain Configuration
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm_chat,
            retriever=vector_db.as_retriever(search_kwargs={"k": 6}),
            memory=memory,
            return_source_documents=True,
            output_key="answer"
        )

        # 5. Execute RAG Retrieval and Generation (Using modern .invoke())
        logger.info(f"Processing query for collection '{collection_name}'")
        result = qa_chain.invoke({"question": query})
        
        answer = result.get("answer", "")
        sources = [
            {"text": doc.page_content, "metadata": doc.metadata} 
            for doc in result.get("source_documents", [])
        ]

        # 6. Structured Output: Lead Extraction
        lead_data = None
        if business_context:
            try:
                # Force the LLM to strictly output the Pydantic schema
                structured_llm = llm_chat.with_structured_output(UniversalLead)
                
                # Proper Prompt Template using variables, preventing prompt injection crashes
                system_prompt = (
                    "You are a Lead Extraction Expert for a business.\n\n"
                    "BUSINESS CONTEXT INSTRUCTIONS:\n{business_context}\n\n"
                    "Analyze the user's latest query and the assistant's reply to determine if this is a lead. "
                    "Extract the data strictly into the provided JSON structure. "
                    "If the user is just asking general info without clear commercial intent, set 'is_lead' to False."
                )
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "User Query: {query}\nAssistant Reply: {answer}")
                ])
                
                extraction_chain = prompt | structured_llm
                
                # Execute extraction via LangChain Expression Language (LCEL)
                lead_data = extraction_chain.invoke({
                    "business_context": business_context,
                    "query": query,
                    "answer": answer
                })
                
            except Exception as extraction_error:
                logger.error(f"Structured lead extraction failed: {extraction_error}", exc_info=True)
                lead_data = None # Failsafe: return the chat answer even if extraction fails

        return {
            "answer": answer,
            "sources": sources,
            "lead_data": lead_data
        }

    except Exception as e:
        logger.error(f"Critical error in core RAG pipeline: {e}", exc_info=True)
        raise