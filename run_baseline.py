import json
from pathlib import Path
from selenium import webdriver
from core.dom_capture import capture_snapshot
from core.snapshot_repository import SnapshotRepository

raiz = Path(__file__).parent
repo = SnapshotRepository(raiz / "snapshots")

driver = webdriver.Chrome()
try:
    driver.get((raiz / "pages" / "login.html").as_uri())
    caminho = repo.save(capture_snapshot(driver), name="login")
finally:
    driver.quit()

print("gravado em:", caminho)
recarregado = repo.load("login")
print("elementos:", len(recarregado["elements"]))
print("primeiro label:", recarregado["elements"][0]["label"])