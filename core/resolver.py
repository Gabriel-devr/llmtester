"""
Tradução de um localizador Selenium para o fingerprint correspondente no baseline.

Responsabilidade:responder "qual elemento do baseline este localizador
endereçava?".

nao conhece a página atual, nao calcula similaridade e nao cura.
Trabalha só sobre dados já capturados.
"""

import re
from dataclasses import dataclass

from selenium.webdriver.common.by import By


class LocatorNaoSuportado(Exception):
    """O tipo de localizador está fora do escopo desta versão."""


@dataclass(frozen=True)
class Resolution:
    fingerprint: dict
    strategy: str      # qual By foi usado
    matched: int       # quantos elementos do baseline casaram


# tag, #id, .classe(s) e um único [attr=valor], nesta ordem
_CSS_SIMPLES = re.compile(
    r"""^\s*
        (?P<tag>[A-Za-z][\w-]*)?
        (?:\#(?P<id>[\w:.-]+))?
        (?P<classes>(?:\.[\w-]+)*)
        (?:\[\s*(?P<attr>[\w-]+)\s*=\s*["']?(?P<valor>[^\]"']*)["']?\s*\])?
        \s*$""",
    re.VERBOSE,
)


def _classes(fingerprint: dict) -> set[str]:
    return set((fingerprint.get("attrs", {}).get("class") or "").split())


def _casa_css_simples(fingerprint: dict, seletor: str) -> bool:
    m = _CSS_SIMPLES.match(seletor)
    if not m or not any(m.group(g) for g in ("tag", "id", "classes", "attr")):
        raise LocatorNaoSuportado(f"CSS fora do subconjunto suportado: {seletor!r}")

    attrs = fingerprint.get("attrs", {})
    if m.group("tag") and fingerprint.get("tag") != m.group("tag").lower():
        return False
    if m.group("id") and attrs.get("id") != m.group("id"):
        return False
    if m.group("classes"):
        exigidas = set(m.group("classes").lstrip(".").split("."))
        if not exigidas <= _classes(fingerprint):
            return False
    if m.group("attr") and attrs.get(m.group("attr")) != m.group("valor"):
        return False
    return True


def _casa(fingerprint: dict, by: str, value: str) -> bool:
    attrs = fingerprint.get("attrs", {})
    texto = fingerprint.get("text") or ""

    if by == By.ID:
        return attrs.get("id") == value
    if by == By.NAME:
        return attrs.get("name") == value
    if by == By.CLASS_NAME:
        return value in _classes(fingerprint)
    if by == By.TAG_NAME:
        return fingerprint.get("tag") == value.lower()
    if by == By.LINK_TEXT:
        return fingerprint.get("tag") == "a" and texto == value
    if by == By.PARTIAL_LINK_TEXT:
        return fingerprint.get("tag") == "a" and value in texto
    if by == By.CSS_SELECTOR:
        return _casa_css_simples(fingerprint, value)
    raise LocatorNaoSuportado(f"Localizador {by!r} ainda não é suportado.")


def resolve(by: str, value: str, snapshot: dict) -> Resolution | None:
    """Devolve a Resolution do primeiro elemento que casa, ou None.

    Levanta LocatorNaoSuportado se o tipo de localizador estiver fora do escopo.
    """
    casados = [fp for fp in snapshot["elements"] if _casa(fp, by, value)]
    if not casados:
        return None
    return Resolution(fingerprint=casados[0], strategy=by, matched=len(casados))