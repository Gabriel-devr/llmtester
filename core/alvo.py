"""
Reconstroi o que um localizador descreve (um fingerprint parcial: so o que ele declara)
e descobre a acao do teste (click, send_keys...).
"""

import linecache
import re

from selenium.webdriver.common.by import By

_VALOR = r"""(?:'([^']*)'|"([^"]*)")"""
_TEXTO = r"(?:text\(\)|normalize-space\((?:\.|text\(\))?\)|\.)"
_ATTR_CSS = re.compile(r"""\[\s*([\w:-]+)\s*([~|^$*]?=)\s*(?:"([^"]*)"|'([^']*)'|([^\]\s]+))\s*\]""")


def _novo() -> dict:
    return {"tag": None, "type": None, "label": None, "text": None,
            "attrs": {}, "extras": {}, "conhecidos": set()}


def _tag(alvo: dict, tag: str | None) -> None:
    if tag and tag != "*":
        alvo["tag"] = tag.lower()
        alvo["conhecidos"].add("tag")


def _texto(alvo: dict, texto: str) -> None:
    if texto:
        alvo["text"] = texto
        alvo["conhecidos"].add("text")


def _atributo(alvo: dict, nome: str, valor: str) -> None:
    if not valor:
        return
    nome = nome.lower()
    if nome == "type":
        alvo["type"] = valor
        alvo["conhecidos"].add("type")
    elif nome in ("id", "name", "placeholder"):
        alvo["attrs"][nome] = valor
        alvo["conhecidos"].add(nome)
    elif nome == "class":
        alvo["attrs"]["class"] = (alvo["attrs"].get("class", "") + " " + valor).strip()
        alvo["conhecidos"].add("class")
    elif nome == "aria-label":
        alvo["label"] = valor
        alvo["conhecidos"].add("label")
    else:
        alvo["extras"][nome] = valor
        alvo["conhecidos"].add("extras")


def _dividir(expressao: str, separador) -> list[str]:
    partes, atual, profundidade, aspas = [], "", 0, None
    for c in expressao.strip():
        if aspas:
            atual += c
            if c == aspas:
                aspas = None
        elif c in "\"'":
            aspas = c
            atual += c
        elif c in "[(":
            profundidade += 1
            atual += c
        elif c in "])":
            profundidade -= 1
            atual += c
        elif profundidade == 0 and separador(c):
            partes.append(atual)
            atual = ""
        else:
            atual += c
    partes.append(atual)
    return [p for p in partes if p.strip()]


def _de_css(seletor: str) -> dict:
    alvo = _novo()
    compostos = _dividir(seletor, lambda c: c.isspace() or c in ">+~")
    composto = compostos[-1] if compostos else ""

    for m in _ATTR_CSS.finditer(composto):
        _atributo(alvo, m.group(1), m.group(3) or m.group(4) or m.group(5) or "")

    simples = re.sub(r":[\w-]+(\([^)]*\))?", "", _ATTR_CSS.sub("", composto))
    _tag(alvo, re.match(r"([A-Za-z][\w-]*|\*)?", simples).group(1))
    for valor in re.findall(r"#([\w-]+)", simples):
        _atributo(alvo, "id", valor)
    for valor in re.findall(r"\.([\w-]+)", simples):
        _atributo(alvo, "class", valor)
    return alvo


def _de_xpath(xpath: str) -> dict:
    alvo = _novo()
    passos = _dividir(xpath, lambda c: c == "/")
    passo = passos[-1] if passos else ""

    m = re.match(r"\s*(?:[\w-]+::)?([A-Za-z][\w:-]*|\*)", passo)
    if m:
        _tag(alvo, m.group(1))
    for m in re.finditer(rf"contains\(\s*@([\w:-]+)\s*,\s*{_VALOR}\s*\)", passo):
        _atributo(alvo, m.group(1), m.group(2) or m.group(3))
    for m in re.finditer(rf"@([\w:-]+)\s*=\s*{_VALOR}", passo):
        _atributo(alvo, m.group(1), m.group(2) or m.group(3))
    m = (re.search(rf"contains\(\s*{_TEXTO}\s*,\s*{_VALOR}\s*\)", passo)
         or re.search(rf"{_TEXTO}\s*=\s*{_VALOR}", passo))
    if m:
        _texto(alvo, m.group(1) or m.group(2))
    return alvo


def fingerprint_do_localizador(by: str, value: str) -> dict | None:
    alvo = _novo()
    if by == By.ID:
        _atributo(alvo, "id", value)
    elif by == By.NAME:
        _atributo(alvo, "name", value)
    elif by == By.CLASS_NAME:
        _atributo(alvo, "class", value)
    elif by == By.TAG_NAME:
        _tag(alvo, value)
    elif by in (By.LINK_TEXT, By.PARTIAL_LINK_TEXT):
        _tag(alvo, "a")
        _texto(alvo, value)
    elif by == By.CSS_SELECTOR:
        alvo = _de_css(value)
    elif by == By.XPATH:
        alvo = _de_xpath(value)
    return alvo if alvo["conhecidos"] else None


def acao_da_chamada(call_site) -> str | None:
    if call_site is None:
        return None
    trecho = "".join(linecache.getline(call_site.file, call_site.line + i) for i in range(3))
    achado = re.search(r"\.(send_keys|click|clear|submit)\s*\(", trecho)
    if achado:
        return achado.group(1)
    if "element_to_be_clickable" in trecho:
        return "click"
    return None
