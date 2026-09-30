import os
from core.adapters.gemini_adapter import gemini_client
from core.llm_healer import curar

llm = gemini_client(api_key=os.environ["GEMINI_API_KEY"])

contexto = "Automacao de login: preenche o campo de senha e clica em entrar."
alvo = {"tag": "input", "type": "password", "label": "Senha", "attrs": {"id": "password"}}
candidatos_fp = [
    {"tag": "input", "type": "text", "label": "Nome completo", "attrs": {"id": "nome"}},
    {"tag": "input", "type": "password", "label": "Senha nova", "attrs": {"id": "senha2"}},
]
candidatos = [(fp, None) for fp in candidatos_fp]

resultado = curar(llm, contexto, alvo, candidatos)
print(resultado)