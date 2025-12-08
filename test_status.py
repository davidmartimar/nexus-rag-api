import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.rag_service import get_document_count

try:
    count = get_document_count()
    print(f"Document count: {count}")
    print("Verification Successful")
except Exception as e:
    print(f"Verification Failed: {e}")
