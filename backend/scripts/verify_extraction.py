import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add the backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.services import chat_service
from app.core.database import init_db

# Mocking History for context
MOCK_HISTORY_CLINIC = [
    {"user": "Hola", "assistant": "Hola, soy el asistente de la clínica. ¿En qué puedo ayudarte?"},
    {"user": "Quiero saber precio de botox", "assistant": "El botox cuesta 300€. ¿Te interesa reservar?"}
]

MOCK_HISTORY_REAL_ESTATE = [
    {"user": "Busco piso", "assistant": "Hola, ¿qué zona te interesa?"},
    {"user": "Zona centro, 2 habitaciones", "assistant": "Tengo uno en Gran Vía por 1200€."}
]

async def verify_extraction():
    print("--- NEXUS LEAD EXTRACTION VERIFICATION (MULTI-TENANT) ---")
    
    # Ensure DB is ready (even if we don't save to it in this direct service test, dependencies might need it)
    await init_db()

    # 1. Test Clinic Context
    print("\n[1] Testing CLINIC Context...")
    clinic_context = "Clínica de Medicina Estética. Ofrecemos Botox, Acido Hialurónico. El objetivo es agendar cita."
    query_clinic = "Si, quiero reservar cita para el botox mañana"
    
    try:
        result_clinic = chat_service.get_answer(
            query=query_clinic,
            history=MOCK_HISTORY_CLINIC,
            business_context=clinic_context
        )
        print("Respuesta LLM:", result_clinic["answer"])
        lead_data = result_clinic.get("lead_data")
        if lead_data:
            print("LEAD DATA EXTRAIDO:", lead_data.model_dump())
            if lead_data.is_lead and "botox" in lead_data.interest_keyword.lower():
                 print("SUCCESS: Contexto Clinica funcionó.")
            else:
                 print("WARNING: Datos no coinciden con lo esperado.")
        else:
            print("FAILURE: No se extrajo lead data.")
            
    except Exception as e:
        print(f"ERROR Clinic: {e}")


    # 2. Test Real Estate Context
    print("\n[2] Testing REAL ESTATE Context...")
    real_estate_context = "Inmobiliaria. Vendemos y alquilamos pisos. Objetivo conseguir teléfono del cliente."
    query_real_estate = "Me interesa verlo. Mi telefono es 666777888."
    
    try:
        result_re = chat_service.get_answer(
            query=query_real_estate,
            history=MOCK_HISTORY_REAL_ESTATE,
            business_context=real_estate_context
        )
        print("Respuesta LLM:", result_re["answer"])
        lead_data_re = result_re.get("lead_data")
        if lead_data_re:
            print("LEAD DATA EXTRAIDO:", lead_data_re.model_dump())
            if lead_data_re.is_lead and ("piso" in lead_data_re.interest_keyword.lower() or "alquiler" in lead_data_re.interest_keyword.lower()):
                 print("SUCCESS: Contexto Inmobiliaria funcionó.")
            else:
                 print("WARNING: Datos no coinciden con lo esperado.")
        else:
            print("FAILURE: No se extrajo lead data.")

    except Exception as e:
        print(f"ERROR Real Estate: {e}")

if __name__ == "__main__":
    asyncio.run(verify_extraction())
