from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from core.interceptor import intercepting

pagina = (Path(__file__).parent / "pages" / "login_v2.html").as_uri()

with intercepting() as it:
    driver = webdriver.Chrome()
    try:
        driver.get(pagina)
        for id_ in ("username", "password", "btn-login"):
            try:
                driver.find_element(By.ID, id_)
            except Exception:
                pass
    finally:
        driver.quit()

print(it.summary())