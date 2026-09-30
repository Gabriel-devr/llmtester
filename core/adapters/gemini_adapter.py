"""
Adapter para usar a api da Gemini
"""

from core.llm_client import LLMClient

MODELO = "gemini-flash-latest"

def gemini_client(api_key: str | None = None, model:str = MODELO) -> LLMClient:
    #Se a api_key nao for passada usamos a variavel de ambiente GEMINI_API_KEY

    from google import genai

    cliente = genai.Client(api_key=api_key)

    def _chamar(prompt:str)-> str:
        respota = cliente.models.generate_content(model=model, contents=prompt)
        return respota.text

    return _chamar