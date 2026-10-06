"""Cura com LLM, o ultimo recurso quando a similaridade nao decide."""

import json

from core.llm_client import LLMClient

def _montar_prompt(contexto: "str | None", by: str, value: str, acao: "str | None", candidatos: list[dict]) -> str:
    candidatos_texto = json.dumps(candidatos, indent=2, ensure_ascii=False)
    contexto_texto = contexto or "(nenhum contexto adicional fornecido)"
    acao_texto = acao or "desconhecida"

    return f"""Um teste de Selenium procura um elemento em uma página web, mas o localizador abaixo não encontra nada (a página provavelmente mudou de estrutura). Não existe registro de como o elemento era antes: deduza qual é o elemento procurado a partir do localizador, da ação e do contexto.

    Contexto do que a automacao faz: {contexto_texto}

    Localizador que falhou: {by} = {value!r}
    Ação que o teste faz com o elemento: {acao_texto}

    Fingerprints dos candidatos encontrados na página atual: {candidatos_texto}

    Responda APENAS com um JSON no formato:
    {{"indice":<numero do candidato correto, ou null se nenhum servir>,"justificativa":"<uma frase curta>"}}
"""

def curar(llm_client: "LLMClient | None", contexto: "str | None", by: str, value: str, acao: "str | None", candidatos: list[tuple[dict, object]]):

    if llm_client is None or not candidatos:
        return None

    fingerprints = [fp for fp, _ in candidatos]
    try:
        texto = (llm_client(_montar_prompt(contexto, by, value, acao, fingerprints)) or "").strip()
        dados = json.loads(texto[texto.find("{"):texto.rfind("}") + 1])
        indice = dados.get("indice")
        if indice is None or not (0 <= indice < len(candidatos)):
            return None
        print(f" [llm] escolheu candidato {indice}: {dados.get('justificativa', '')}")
        return candidatos[indice][1]
    except Exception as erro:
        print(f' [llm] falhou ao consultar a LLM: {erro}')
        return None
