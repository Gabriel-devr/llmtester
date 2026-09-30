"""
Aqui iremos verificar a similaridade entre os fingerprints que o dom_capture.py produz
"""

import difflib
from dataclasses import dataclass

#Pesos de cada caracteristica na nota final

PESOS = {
    "tag":2,
    "type": 2,
    "label": 3,
    "name": 2,
    "id": 1,
    "placeholder": 1,
    "text": 1,
    "form_index": 2,
}

@dataclass(frozen=True)
class Candidato:
    fingerprint: dict
    elemento: object
    pontuacao: float

def _texto_parecido(a,b) -> float:
    a, b = (a or "").strip().lower(), (b or "").strip().lower()
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()

def _igual(a,b) -> float:
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    return 1.0 if a==b else 0.0

def pontuar(alvo: dict, candidato: dict) -> float:
    attrs_alvo = alvo.get("attrs", {})
    attrs_cand = candidato.get("attrs", {})

    notas = {
        "tag": _igual(alvo.get("tag"), candidato.get("tag")),
        "type": _igual(alvo.get("type"), candidato.get("type")),
        "label": _texto_parecido(alvo.get("label"), candidato.get("label")),
        "name": _texto_parecido(attrs_alvo.get("name"), attrs_cand.get("name")),
        "id": _texto_parecido(attrs_alvo.get("id"), attrs_cand.get("id")),
        "placeholder": _texto_parecido(attrs_alvo.get("placeholder"), attrs_cand.get("placeholder")),
        "text": _texto_parecido(alvo.get("text"), candidato.get("text")),
        "form_index": _igual(alvo.get("form_index"), candidato.get("form_index")),
    }

    pontos = sum(PESOS[chave] * nota for chave, nota in notas.items())
    peso_total = sum(PESOS.values())
    return pontos / peso_total

def melhor_candidato(alvo: dict, candidatos: list[tuple[dict, object]]) -> "Candidato | None":
    melhor = None
    for fingerprint, elemento in candidatos:
        pontuacao = pontuar(alvo, fingerprint)
        if melhor is None or pontuacao > melhor.pontuacao:
            melhor = Candidato(fingerprint=fingerprint, elemento=elemento, pontuacao=pontuacao)
    return melhor