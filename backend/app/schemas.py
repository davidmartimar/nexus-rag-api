from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class UniversalLead(BaseModel):
    """
    Schema universal para captación de leads en cualquier sector (Clínica, Inmobiliaria, Legal, etc).
    """
    is_lead: bool = Field(description="¿El usuario ha mostrado intención clara de compra, reserva o contacto?")
    contact_name: Optional[str] = Field(None, description="Nombre del usuario si lo ha proporcionado.")
    contact_info: Optional[str] = Field(None, description="Email o teléfono si lo ha proporcionado.")
    interest_keyword: str = Field(description="Palabra clave canoníca de qué busca (Ej: 'Botox', 'Alquiler T4', 'Divorcio').")
    summary_note: str = Field(description="Resumen comercial de 1 frase (Max 15 palabras) con lo esencial para la venta.")
    urgency_level: Literal["High", "Medium", "Low"] = Field(description="Nivel de urgencia detectado en el lenguaje del usuario.")

class ChatRequest(BaseModel):
    message: str
    collection_name: Optional[str] = "nexus_slot_1"
    history: List[dict] = []
    # Nuevo campo para contexto dinámico
    business_context: Optional[str] = Field(
        None, 
        description="Instrucciones específicas del negocio para la extracción de leads. Ej: 'Esto es una clínica dental, busca tratamientos como implantes o brackets'."
    )
    # Token opcional para identificar sesión/usuario si se requiere
    user_id: Optional[str] = None 


class UsageMetadata(BaseModel):
    """Metadatos de uso de la cuota diaria."""
    daily_limit: int = Field(description="Límite máximo de mensajes por día.")
    current_usage: int = Field(description="Mensajes consumidos hoy.")
    remaining: int = Field(description="Mensajes restantes antes del bloqueo.")
    is_limit_reached: bool = Field(description="True si el usuario ha agotado su cuota.")

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    lead_data: Optional[UniversalLead] = None
    usage: Optional[UsageMetadata] = None

