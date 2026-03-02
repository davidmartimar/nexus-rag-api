import sys
import importlib

packages = [
    "langchain",
    "langchain_community",
    "langchain_text_splitters",
    "langchain_openai",
    "chromadb",
    "pypdf",
    "fastapi",
    "uvicorn"
]

print("--- VERIFYING IMPORTS ---")
for package in packages:
    try:
        importlib.import_module(package)
        print(f"SUCCESS: {package} imported.")
    except ImportError as e:
        print(f"FAILURE: {package} NOT FOUND. Error: {e}")
    except Exception as e:
        print(f"FAILURE: {package} ERROR. Error: {e}")
