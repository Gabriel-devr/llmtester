"""
Aqui ocorre a cura com LLM, o último recurso para quando o matcher.py não encontrou um candidato de confiança suficiente.
"""
#Futuramente dá pra implementar difentes LLMs, pois llm_healer só monta o prompt e chama o 'llm_client(prompt)

import json

from core.llm_client import LLMClient

def _montar_prompt(context: "str | None", alvo: dict, candidatos: list[dict])->str:
    candidatos_texto = json.dumps(candidatos, indent=2, ensure_ascii=False)
    alvo_texto = json.dumps(alvo, indent=2, ensure_ascii=False)
    contexto_texto = context or "(nenhum contexto adicional fornecido)"

    return f"""Um teste de Selenium procura um elemento em uma página web cujo localizador original parou de funcionar (provavelmente a página mudou de estrutura).

    Contexto do que a automacao faz: {contexto_texto}

    Fingerprint do elemento como ele era antes (baseline):
    {alvo_texto}

    Fingerprints do candidatos encontrados na página atual: {candidatos_texto}

    Responda APENAS com um JSON no formato:
    {{"indice":<numero do candidato correto, ou null se nenhum servir>,"justificativa":"<uma frase curta>"}}
"""

def curar(llm_client: "LLMClient | None", contexto: "str | None", alvo: dict, candidatos: list[tuple[dict, object]]):

    if llm_client is None or not candidatos:
        return None

    fingerprints = [fp for fp, _ in candidatos]
    prompt = _montar_prompt(contexto, alvo, fingerprints)

    try:
        texto = llm_client(prompt).strip()
        dados = json.loads(texto)
        indice = dados.get("indice")
        if indice is None or not (0 <= indice < len(candidatos)):
            return None
        print(f" [lllm] escolheu candidato {indice}: {dados.get('justificativa', '')}")
        return candidatos[indice][1]
    except Exception as erro:
        print(f' [llm] falhou ao consultar a LLM: {erro}')
        return None