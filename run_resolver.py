from pathlib import Path
from selenium.webdriver.common.by import By
from core.resolver import resolve, LocatorNaoSuportado
from core.snapshot_repository import SnapshotRepository

repo = SnapshotRepository(Path(__file__).parent / "snapshots")
baseline = repo.load("login")

casos = [
    (By.ID, "username"),
    (By.ID, "password"),
    (By.ID, "btn-login"),
    (By.NAME, "login_button"),
    (By.CSS_SELECTOR, "input#username"),
    (By.TAG_NAME, "input"),
    (By.ID, "nao-existe"),
    (By.XPATH, "//input[1]"),
]

for by, value in casos:
    try:
        r = resolve(by, value, baseline)
    except LocatorNaoSuportado as e:
        print(f"{by:>12}={value:<20} -> NÃO SUPORTADO ({e})")
        continue
    if r is None:
        print(f"{by:>12}={value:<20} -> ausente no baseline")
    else:
        fp = r.fingerprint
        identidade = fp.get("label") or fp.get("text") or "(sem rótulo)"
        print(f"{by:>12}={value:<20} -> {fp['tag']}/{fp.get('type')} "
              f"{identidade!r} (casaram: {r.matched})")