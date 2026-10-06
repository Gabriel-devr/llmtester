import time

from core.llm_client import LLMClient

MODELO = "gemini-flash-latest"

def gemini_client(api_key: str | None = None, model: str = MODELO, tentativas: int = 3) -> LLMClient:
    from google import genai

    cliente = genai.Client(api_key=api_key)

    def _chamar(prompt: str) -> str:
        for tentativa in range(tentativas):
            try:
                return cliente.models.generate_content(model=model, contents=prompt).text
            except Exception as erro:
                if tentativa == tentativas - 1:
                    raise
                espera = 2 ** tentativa
                print(f" [gemini] falhou ({erro}); tentando de novo em {espera}s")
                time.sleep(espera)

    return _chamar
