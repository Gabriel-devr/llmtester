import json
from pathlib import Path
from selenium import webdriver
from core.dom_capture import capture_snapshot

pagina = (Path(__file__).parent / "pages" / "login.html").as_uri()

driver = webdriver.Chrome()
try:
    driver.get(pagina)
    snapshot = capture_snapshot(driver)
finally:
    driver.quit()

print(json.dumps(snapshot, indent=2, ensure_ascii=False))