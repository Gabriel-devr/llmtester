import time

from core.llm_client import LLMClient

MODELO = "openai/gpt-oss-20b"

def groq_client(api_key: str | None = None, model: str = MODELO, tentativas: int = 3) -> LLMClient:
    from groq import Groq

    cliente = Groq(api_key=api_key)

    def _chamar(prompt: str) -> str:
        for tentativa in range(tentativas):
            try:
                resposta = cliente.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resposta.choices[0].message.content
            except Exception as erro:
                if tentativa == tentativas - 1:
                    raise
                espera = 2 ** tentativa
                print(f" [groq] falhou ({erro}); tentando de novo em {espera}s")
                time.sleep(espera)

    return _chamar