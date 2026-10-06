"""Nota de semelhanca entre o alvo (o que o localizador descreve) e cada candidato."""

import difflib
from dataclasses import dataclass

PESOS = {
    "tag": 2,
    "type": 2,
    "label": 3,
    "name": 2,
    "id": 1,
    "placeholder": 1,
    "text": 4,
    "class": 0.5,
    "extras": 2,
}

EVIDENCIA_PLENA = 6
MARGEM_MINIMA = 0.1


@dataclass(frozen=True)
class Candidato:
    elemento: object
    pontuacao: float
    margem: float
    ambigua: bool


def _igual(a, b) -> float:
    return 1.0 if a == b else 0.0


def _texto_parecido(a, b) -> float:
    a, b = (a or "").strip().lower(), (b or "").strip().lower()
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def _texto_natural(a, b) -> float:
    nota = _texto_parecido(a, b)
    if nota == 0.0:
        return nota
    palavras_a, palavras_b = set(a.lower().split()), set(b.lower().split())
    return (nota + len(palavras_a & palavras_b) / len(palavras_a | palavras_b)) / 2


def _texto_contido(a, b) -> float:
    nota = _texto_natural(a, b)
    a, b = a.strip().lower(), (b or "").strip().lower()
    return max(nota, 0.85) if len(a) >= 3 and a in b else nota


def _classes_contidas(a, b) -> float:
    a, b = set(a.split()), set((b or "").split())
    return len(a & b) / len(a)


def evidencia(alvo: dict) -> float:
    return min(1.0, sum(PESOS[d] for d in alvo["conhecidos"]) / EVIDENCIA_PLENA)


def pontuar(alvo: dict, candidato: dict) -> float:
    attrs_alvo = alvo["attrs"]
    attrs_cand = candidato.get("attrs", {})
    conhecidos = alvo["conhecidos"]

    notas = {}
    if "tag" in conhecidos:
        notas["tag"] = _igual(alvo["tag"], candidato.get("tag"))
    if "type" in conhecidos:
        notas["type"] = _igual(alvo["type"], candidato.get("type"))
    if "label" in conhecidos:
        notas["label"] = _texto_natural(alvo["label"], candidato.get("label") or attrs_cand.get("aria-label"))
    for dimensao in ("name", "id", "placeholder"):
        if dimensao in conhecidos:
            notas[dimensao] = _texto_parecido(attrs_alvo[dimensao], attrs_cand.get(dimensao))
    if "text" in conhecidos:
        notas["text"] = _texto_contido(alvo["text"], candidato.get("text"))
    if "class" in conhecidos:
        notas["class"] = _classes_contidas(attrs_alvo["class"], attrs_cand.get("class"))
    if "extras" in conhecidos:
        similares = [_texto_parecido(v, attrs_cand.get(k)) for k, v in alvo["extras"].items()]
        notas["extras"] = sum(similares) / len(similares)

    return sum(PESOS[d] * nota for d, nota in notas.items()) / sum(PESOS[d] for d in notas)


def _texto(fingerprint: dict) -> str:
    return (fingerprint.get("text") or "").strip().lower()


def melhor_candidato(alvo: dict, candidatos: list[tuple[dict, object]], margem_minima: float = MARGEM_MINIMA) -> "Candidato | None":
    pontuados = sorted(
        ((pontuar(alvo, fingerprint), fingerprint, elemento) for fingerprint, elemento in candidatos),
        key=lambda item: item[0],
        reverse=True,
    )
    if not pontuados:
        return None
    pontuacao, fingerprint, elemento = pontuados[0]
    margem = pontuacao - pontuados[1][0] if len(pontuados) > 1 else pontuacao

    texto_alvo = _texto(alvo)
    texto_igual_em_outro = bool(texto_alvo) and _texto(fingerprint) != texto_alvo and any(
        _texto(outro) == texto_alvo for _, outro, _ in pontuados[1:]
    )
    return Candidato(elemento, pontuacao, margem, margem < margem_minima or texto_igual_em_outro)
