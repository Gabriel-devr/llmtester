from selenium import webdriver
from core.dom_capture import capture_candidates
from core.snapshot_repository import SnapshotRepository
from core.resolver import resolve
from core.matcher import melhor_candidato
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()

repo = SnapshotRepository("snapshots")
baseline = repo.load("login")  

driver.get("file:///C:/Users/Gabriel/Desktop/INICIACAO%20CIENTIFCA/pages/login_v2.html")

resolucao = resolve(By.ID, "username", baseline) #antes
candidatos = capture_candidates(driver) #agora

melhor = melhor_candidato(resolucao.fingerprint, candidatos)
print("pontuacao:", melhor.pontuacao)
print("candidato escolhido, attrs:", melhor.fingerprint["attrs"])
melhor.elemento.send_keys("teste@gmail.com")

driver.quit()