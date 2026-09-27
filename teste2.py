from selenium import webdriver
from core.dom_capture import capture_snapshot
from core.snapshot_repository import SnapshotRepository

driver = webdriver.Chrome()
driver.get("file:///C:/Users/Gabriel/Desktop/INICIACAO%20CIENTIFCA/pages/login.html")

repo = SnapshotRepository("snapshots")
caminho = repo.save(capture_snapshot(driver), name="login")
print("salvo em:", caminho)

carregado = repo.load("login")
print("elementos carregados:", len(carregado["elements"]))

driver.quit()