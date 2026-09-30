import os
from google import genai

cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

for modelo in cliente.models.list():
    print(modelo.name)