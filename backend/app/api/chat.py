from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import logging

# Servicios y Core
from app.services.chat_service import get_answer
from app.core.database import get_db_connection
from app.core.security import hash_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

# --- MODELO UNIFICADO (Satisface a Antigravity y a n8n) ---
class QueryRequest(BaseModel):
    # Campos principales (Frontend v4.1)
    message: Optional[str] = None
    collection_name: str = "nexus_slot_1" # Default sugerido por Antigravity
    
    # Campos de Negocio / Contexto
    business_context: Optional[str] = None
    user_id: Optional[str] = None

    # Campos Legacy (Compatibilidad n8n antigua)
    query: Optional[str] = None 
    system_instruction: Optional[str] = None

# --- FUNCIÓN DE GUARDADO EN SEGUNDO PLANO ---
async def save_interaction(user_id: str, user_msg: str, bot_msg: str):
    """Guarda la interacción sin bloquear la respuesta al usuario."""
    if not user_id:
        return
    try:
        user_hash = hash_user_id(user_id)
        # Guardamos en la BDD persistente (/app/data/nexus.db)
        async with get_db_connection() as db:
            await db.execute(
                "INSERT INTO chat_sessions (session_id, role, content_encrypted) VALUES (?, ?, ?)",
                (user_hash, "user", user_msg.encode())
            )
            await db.execute(
                "INSERT INTO chat_sessions (session_id, role, content_encrypted) VALUES (?, ?, ?)",
                (user_hash, "assistant", bot_msg.encode())
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Error guardando historial background: {e}")

# --- ENDPOINT ---
@router.post("/chat", tags=["Chat"])
async def chat_endpoint(request: QueryRequest, background_tasks: BackgroundTasks):
    # 1. Normalizar entrada (message gana, query es fallback)
    final_query = request.message or request.query
    final_context = request.business_context or request.system_instruction
    
    if not final_query:
        raise HTTPException(status_code=400, detail="Message/Query cannot be empty")

    try:
        # 2. Llamar al Cerebro (usando la collection_name que pide Antigravity)
        response = get_answer(
            query=final_query, 
            collection_name=request.collection_name, 
            history=[] # Stateless por ahora para estabilidad
        )
        
        # 3. Procesar respuesta
        bot_answer = ""
        lead_data = None
        
        if isinstance(response, dict):
            bot_answer = response.get("answer", "")
            lead_data = response.get("lead_data", None)
        else:
            bot_answer = str(response)

        # 4. Guardar log si hay user_id (Background)
        if request.user_id:
            background_tasks.add_task(
                save_interaction, 
                request.user_id, 
                final_query, 
                bot_answer
            )

        # 5. Respuesta final
        return {
            "answer": bot_answer,
            "lead_data": lead_data,
            "usage": {"remaining": 20, "limit_reached": False}
        }
        
    except Exception as e:
        logger.error(f"ERROR CRÍTICO EN CHAT: {e}")
        raise HTTPException(status_code=500, detail=str(e))