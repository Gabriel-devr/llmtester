from selenium import webdriver
from core.dom_capture import capture_snapshot

driver = webdriver.Chrome()
driver.get("file:///C:/Users/Gabriel/Desktop/INICIACAO%20CIENTIFCA/pages/login.html")
import json
print(json.dumps(capture_snapshot(driver), indent=2, ensure_ascii=False))
driver.quit()