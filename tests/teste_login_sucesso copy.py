from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get(r"file:///C:/fredduraosourcecode/login_v2.html")

user_box = driver.find_element(by=By.ID, value="username")
user_box.send_keys("teste@gmail.com")

password_box = driver.find_element(by=By.ID, value="password")
password_box.send_keys("gabriel123")

submit_button = driver.find_element(by=By.ID, value="btn-login")
submit_button.click()

WebDriverWait(driver, 5).until(EC.url_contains("sucesso.html"))

assert "sucesso.html" in driver.current_url, "Falha: o login não navegou para a página de sucesso"

titulo = driver.title
print("Titulo da página:", titulo)

input("Pressione Enter para fechar o navegador...")
driver.quit()