import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
from app.schemas import UniversalLead

# Configuration
CHROMA_DB_DIR = "/app/chroma_db"
from app.services.rag_service import DEFAULT_COLLECTION_NAME

def get_answer(query: str, collection_name: str = DEFAULT_COLLECTION_NAME, history: list = [], business_context: str = None):
    """
    1. Embeds the query.
    2. Searches ChromaDB for relevant chunks.
    3. Sends chunks + query + history to LLM for Answer.
    4. (Parallel/Post) Sends context to LLM for Lead Extraction.
    5. Returns answer + sources + lead_data.
    """
    try:
        # 1. Initialize Vector DB Connection
        embeddings = OpenAIEmbeddings()
        vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )

        # 2. Initialize LLM (The Brain)
        llm_chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        
        # 3. Initialize Memory
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", 
            return_messages=True, 
            k=5,
            output_key="answer"
        )
        
        # Reconstruct Memory from History
        for exchange in history:
            if "user" in exchange and "assistant" in exchange:
                memory.save_context(
                    {"input": exchange["user"]}, 
                    {"answer": exchange["assistant"]}
                )

        # 4. RAG Chain for Answer
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm_chat,
            retriever=vector_db.as_retriever(search_kwargs={"k": 6}),
            memory=memory,
            return_source_documents=True,
            output_key="answer"
        )

        # 5. Ask the question (RAG)
        result = qa_chain({"question": query})
        answer = result["answer"]
        sources = [{"text": doc.page_content, "metadata": doc.metadata} for doc in result["source_documents"]]

        # 6. Extract Lead Data (Multi-Tenant / Business Agnostic)
        lead_data = None
        if business_context:
            try:
                # Prepare a focused extraction prompt
                # We analyze the LAST interaction (query + answer) mainly, 
                # but might need history if provided. 
                extraction_llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
                structured_llm = extraction_llm.with_structured_output(UniversalLead)
                
                system_prompt = f"""
                You are a Lead Extraction Expert for a business.
                
                BUSINESS CONTEXT INSTRUCTIONS:
                "{business_context}"
                
                Analyze the user's latest message and the assistant's reply to determine if this is a lead.
                Extract the data into the JSON structure provided.
                If the user is just asking general info without clear intent, set 'is_lead' to False.
                """
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", f"User Query: {query}\nAssistant Reply: {answer}")
                ])
                
                chain = prompt | structured_llm
                lead_data = chain.invoke({})
                
            except Exception as e:
                print(f"Lead extraction failed: {e}")
                # We do not fail the main request if extraction fails
                lead_data = None

        return {
            "answer": answer,
            "sources": sources,
            "lead_data": lead_data
        }

    except Exception as e:
        print(f"Error generating answer: {e}")
        raise e