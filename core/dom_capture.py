import re

_SELETOR_CANDIDATOS = "input, button, a, select, textarea, [role]"
_TAGS_PADRAO = {"input", "button", "a", "select", "textarea"}

# via JavaScript: find_elements + get_attribute seriam uma ida e volta ao navegador por atributo
_DESCREVER_JS = r"""
const descrever = (el) => {
    const r = el.getBoundingClientRect();
    const lbl = el.id
        ? document.querySelector('label[for="' + CSS.escape(el.id) + '"]')
        : el.closest('label');
    return {
        tag: el.tagName.toLowerCase(),
        type: el.type || null,
        text: (el.innerText || el.value || '').trim().slice(0, 200),
        label: lbl ? lbl.innerText.trim() : null,
        attrs: Object.fromEntries(
            Array.from(el.attributes).map(a => [a.name, a.value])),
        visible: !!(r.width && r.height)
    };
};
"""

_EXTRACTOR_JS = _DESCREVER_JS + r"""
const SELETOR = arguments[0];
return Array.from(document.querySelectorAll(SELETOR)).map(
    el => ({node: el, fingerprint: descrever(el)}));
"""

_ELEMENTO_JS = _DESCREVER_JS + "return descrever(arguments[0]);"


def seletor_candidatos(tag: str | None = None) -> str:
    if tag and tag not in _TAGS_PADRAO and re.fullmatch(r"[a-z][a-z0-9-]*", tag):
        return f"{_SELETOR_CANDIDATOS}, {tag}"
    return _SELETOR_CANDIDATOS


def capture_fingerprint(driver, elemento) -> dict:
    return driver.execute_script(_ELEMENTO_JS, elemento)


def capture_candidates(driver, seletor: str = _SELETOR_CANDIDATOS):
    linhas = driver.execute_script(_EXTRACTOR_JS, seletor)
    return [(linha["fingerprint"], linha["node"]) for linha in linhas]
