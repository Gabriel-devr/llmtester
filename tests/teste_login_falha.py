from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get(r"file:///C:/fredduraosourcecode/login.html")

user_box = driver.find_element(by=By.ID, value="username")
user_box.send_keys("testeteste@gmail.com")

password_box = driver.find_element(by=By.ID, value="password")
password_box.send_keys("gabriel123")

submit_button = driver.find_element(by=By.ID, value="btn-login")
submit_button.click()

assert "sucesso.html" not in driver.current_url, "Falha de seguranca: credencial invalida foi aceita e navegou para a pagina de sucesso"
assert "login.html" in driver.current_url, "Erro: A página atual não é a tela de login esperada."

is_valid = driver.execute_script("return arguments[0].checkValidity();", user_box)
assert not is_valid, "Erro: O campo de usuário aceitou um e-mail fora do padrão definido."

print("Sucesso: O fluxo negativo bloqueou o acesso corretamente.")

driver.quit()