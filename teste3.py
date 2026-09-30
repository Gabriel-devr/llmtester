from core.resolver import resolve, LocatorNaoSuportado
from core.snapshot_repository import SnapshotRepository
from selenium.webdriver.common.by import By

repo = SnapshotRepository("snapshots")
baseline = repo.load("login")

resolucao = resolve(By.ID, "username", baseline)
print(resolucao.fingerprint["label"]) 
print(resolucao.matched)

nada = resolve(By.ID, "nao-existe", baseline)
print(nada)

try:
    resolve(By.XPATH, "//input", baseline)
except LocatorNaoSuportado as e:
    print("esperado:", e)