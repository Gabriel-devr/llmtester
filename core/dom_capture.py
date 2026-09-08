"""
Captura de fingerprints de elementos a partir do DOM renderizado.

perguntar ao navegador quais elementos interagíveis
existem na página e descrever cada um deles.
"""

from datetime import datetime, timezone

SCHEMA_VERSION = 1

_SELETOR_CANDIDATOS = "input, button, a, select, textarea, [role]"

_EXTRACTOR_JS = r"""
const SELETOR = arguments[0];
return Array.from(document.querySelectorAll(SELETOR)).map((el, i) => {
  const r = el.getBoundingClientRect();
  const lbl = el.id
      ? document.querySelector('label[for="' + CSS.escape(el.id) + '"]')
      : el.closest('label');
  return {
    node: el,
    fingerprint: {
      index: i,
      tag: el.tagName.toLowerCase(),
      type: el.type || null,
      text: (el.innerText || el.value || '').trim().slice(0, 200),
      label: lbl ? lbl.innerText.trim() : null,
      attrs: Object.fromEntries(
          Array.from(el.attributes).map(a => [a.name, a.value])),
      form_index: el.form ? Array.from(el.form.elements).indexOf(el) : -1,
      rect: {
        x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height)
      },
      visible: !!(r.width && r.height)
    }
  };
});
"""


def capture_candidates(driver, seletor: str = _SELETOR_CANDIDATOS):
    """Devolve [(fingerprint, WebElement), ...] da página atual.
    """
    linhas = driver.execute_script(_EXTRACTOR_JS, seletor)
    return [(linha["fingerprint"], linha["node"]) for linha in linhas]


def capture_fingerprints(driver, seletor: str = _SELETOR_CANDIDATOS) -> list[dict]:
    return [fp for fp, _ in capture_candidates(driver, seletor)]


def capture_snapshot(driver, seletor: str = _SELETOR_CANDIDATOS) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": driver.current_url,
        "title": driver.title,
        "selector_scope": seletor,
        "elements": capture_fingerprints(driver, seletor),
    }