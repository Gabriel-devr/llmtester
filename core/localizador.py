"""
Gera um localizador novo para o elemento curado; so vale se, na pagina,
ele encontra exatamente aquele elemento.
"""

from selenium.webdriver.common.by import By

_ATRIBUTOS_ESTAVEIS = ("data-testid", "data-test", "data-qa", "name", "aria-label", "placeholder")


_CAMPOS_DE_ENTRADA = {"input", "textarea", "select"}


def _literal_xpath(texto: str) -> str | None:
    for aspas in ("'", '"'):
        if aspas not in texto:
            return f"{aspas}{texto}{aspas}"
    return None


def _css_attr(tag: str, atributo: str, valor: str) -> str:
    escapado = valor.replace("\\", "\\\\").replace('"', '\\"')
    return f'{tag}[{atributo}="{escapado}"]'


def melhor_localizador(driver, elemento, fingerprint: dict) -> tuple[str, str] | None:
    attrs = fingerprint.get("attrs", {})
    tag = fingerprint.get("tag") or "*"

    candidatos = []
    if attrs.get("id"):
        candidatos.append((By.ID, attrs["id"]))
    for atributo in _ATRIBUTOS_ESTAVEIS:
        if attrs.get(atributo):
            candidatos.append((By.CSS_SELECTOR, _css_attr(tag, atributo, attrs[atributo])))

    texto = (fingerprint.get("text") or "").strip()
    if tag not in _CAMPOS_DE_ENTRADA and tag != "*" and 0 < len(texto) <= 80 and "\n" not in texto:
        literal = _literal_xpath(texto)
        if literal:
            candidatos.append((By.XPATH, f"//{tag}[normalize-space()={literal}]"))

    for by, value in candidatos:
        try:
            achados = driver.find_elements(by, value)
        except Exception:
            continue
        if len(achados) == 1 and achados[0] == elemento:
            return by, value
    return None
