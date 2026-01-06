import langchain
import os
print(f"Langchain path: {langchain.__path__}")
print(f"Dir: {os.listdir(langchain.__path__[0])}")
