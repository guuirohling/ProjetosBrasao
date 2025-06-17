from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions

EDGE_DRIVER_PATH = r"C:\Users\guuir\OneDrive\Atendimentos\EMPRESA LARISSA\Renomeador_de_arquivos\msedgedriver.exe"

options = EdgeOptions()
options.add_argument("--user-data-dir=edge-data")  # Mantém o login salvo, mas é opcional

driver = webdriver.Edge(service=EdgeService(EDGE_DRIVER_PATH), options=options)
driver.get("https://www.google.com")
input("Se abriu o Edge com o Google, o driver está OK. Pressione Enter para fechar.")
driver.quit()
