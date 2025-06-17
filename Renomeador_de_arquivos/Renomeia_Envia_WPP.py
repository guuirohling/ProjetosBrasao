import sys
import os
import re
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QHBoxLayout, QMessageBox, QAbstractItemView,
    QDialog, QLabel
)
from PyQt5.QtCore import Qt
from PyPDF2 import PdfReader

# >>>> CONFIGURAÇÕES DO EDGE <<<<
WHATSAPP_PADRAO = "48999737585"  # Telefone padrão sem parênteses, só números
#EDGE_DRIVER_PATH = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")
EDGE_DRIVER_PATH = os.path.join(os.path.dirname(sys.executable), "msedgedriver.exe")
# ----------- Funções de extração -----------

def extract_tomador_nome_telefone(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        bloco = re.search(r'TOMADOR DE SERVIÇOS(.*?)(?:DISCRIMINAÇÃO DOS SERVIÇOS|VALOR TOTAL DA NFS-e)', text, re.DOTALL | re.IGNORECASE)
        nome, telefone = "Nao Encontrado", ""
        if bloco:
            linhas = [linha.strip() for linha in bloco.group(1).split('\n') if linha.strip()]
            for i, linha in enumerate(linhas):
                if re.match(r'\d{3}\.\d{3}\.\d{3}-\d{2}', linha):
                    # Nome está na próxima linha
                    if i + 1 < len(linhas):
                        nome = linhas[i + 1]
                        nome = re.sub(r'[\\/:*?"<>|]', '', nome)
                    # Telefone está 3 linhas abaixo
                    if i + 4 < len(linhas):
                        tel_linha = linhas[i + 4]
                        match_tel = re.search(r'(\(?\d{2}\)?\s?\d{4,5}-?\d{4})', tel_linha)
                        if match_tel:
                            telefone = re.sub(r'\D', '', match_tel.group(1))  # Só números
        if not telefone or len(telefone) < 10:
            telefone = WHATSAPP_PADRAO
        return nome, telefone
    except Exception as e:
        print(f"Erro ao ler {pdf_path}: {e}")
        return "Nao Encontrado", WHATSAPP_PADRAO

# ----------- Função para abrir Edge e carregar WhatsApp Web -----------

def abrir_whatsapp_web(edgedriver_path=EDGE_DRIVER_PATH):
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.edge.options import Options as EdgeOptions

    options = EdgeOptions()
    # options.add_argument("--user-data-dir=edge-data")  # Ative se quiser manter o login
    options.add_argument("--disable-features=msEdgeProfileFormSupport")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-software-rasterizer")

    driver = webdriver.Edge(service=EdgeService(edgedriver_path), options=options)
    driver.get("https://web.whatsapp.com/")
    return driver

# ----------- Interface PyQt -----------

class PDFRenomeador(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Renomeador de PDFs NFS-e + WhatsApp (Edge)")
        self.resize(1050, 420)
        self.pdf_list = []
        self.destino = ""

        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.btn_importar = QPushButton("Importar PDFs")
        self.btn_destino = QPushButton("Selecionar pasta destino")
        self.btn_processar = QPushButton("Processar")
        self.btn_whatsapp = QPushButton("Enviar via WhatsApp")
        btn_layout.addWidget(self.btn_importar)
        btn_layout.addWidget(self.btn_destino)
        btn_layout.addWidget(self.btn_processar)
        btn_layout.addWidget(self.btn_whatsapp)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Selecionar", "Nome Original", "Nome Sugerido", "Editar Nome Final", "Telefone"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_importar.clicked.connect(self.importar_pdfs)
        self.btn_destino.clicked.connect(self.selecionar_destino)
        self.btn_processar.clicked.connect(self.processar)
        self.btn_whatsapp.clicked.connect(self.enviar_whatsapp_selecionados)

    def importar_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF Files (*.pdf)")
        for file in files:
            if file not in [row[0] for row in self.pdf_list]:
                nome_tomador, telefone = extract_tomador_nome_telefone(file)
                nome_sugerido = f"NF - {nome_tomador}.pdf"
                self.pdf_list.append([file, os.path.basename(file), nome_sugerido, nome_sugerido, True, telefone])
        self.atualiza_tabela()

    def atualiza_tabela(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for row_idx, (filepath, nome_original, nome_sugerido, nome_final, selecionado, telefone) in enumerate(self.pdf_list):
            self.table.insertRow(row_idx)
            checkbox = QCheckBox()
            checkbox.setChecked(selecionado)
            checkbox.stateChanged.connect(lambda state, idx=row_idx: self.checkbox_changed(idx, state))
            self.table.setCellWidget(row_idx, 0, checkbox)
            item_nome_ori = QTableWidgetItem(nome_original)
            item_nome_ori.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 1, item_nome_ori)
            item_nome_sug = QTableWidgetItem(nome_sugerido)
            item_nome_sug.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 2, item_nome_sug)
            item_nome_final = QTableWidgetItem(nome_final)
            self.table.setItem(row_idx, 3, item_nome_final)
            item_tel = QTableWidgetItem(telefone)
            self.table.setItem(row_idx, 4, item_tel)
        self.table.blockSignals(False)
        self.table.cellChanged.connect(self.nome_final_editado)

    def checkbox_changed(self, idx, state):
        self.pdf_list[idx][4] = bool(state)

    def nome_final_editado(self, row, column):
        if column == 3:
            novo_nome = self.table.item(row, 3).text()
            self.pdf_list[row][3] = novo_nome
        elif column == 4:
            novo_tel = self.table.item(row, 4).text()
            self.pdf_list[row][5] = novo_tel

    def selecionar_destino(self):
        destino = QFileDialog.getExistingDirectory(self, "Selecionar pasta destino")
        if destino:
            self.destino = destino

    def processar(self):
        if not self.destino:
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta destino!")
            return
        processados = 0
        for filepath, _, _, nome_final, selecionado, _ in self.pdf_list:
            if selecionado:
                novo_caminho = os.path.join(self.destino, nome_final)
                try:
                    with open(filepath, "rb") as src, open(novo_caminho, "wb") as dst:
                        dst.write(src.read())
                    processados += 1
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Erro ao processar {filepath}: {e}")
        QMessageBox.information(self, "Processamento finalizado", f"{processados} arquivos processados!")

    def aguardar_whatsapp_carregar(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Aguardando WhatsApp Web")
        layout = QVBoxLayout()
        label = QLabel("Por favor, faça login no WhatsApp Web no navegador Edge aberto.\nQuando estiver tudo pronto, clique em OK para iniciar o envio.")
        layout.addWidget(label)
        btn_ok = QPushButton("OK")
        layout.addWidget(btn_ok)
        btn_ok.clicked.connect(dialog.accept)
        dialog.setLayout(layout)
        dialog.exec_()

    def enviar_whatsapp_selecionados(self):
        if not self.destino:
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta destino!")
            return
        lista_envio = []
        for filepath, _, _, nome_final, selecionado, telefone in self.pdf_list:
            if selecionado:
                novo_caminho = os.path.join(self.destino, nome_final)
                if not os.path.isfile(novo_caminho):
                    with open(filepath, "rb") as src, open(novo_caminho, "wb") as dst:
                        dst.write(src.read())
                lista_envio.append((novo_caminho, telefone))
        mensagem = "Olá!\nSegue sua nota fiscal referente aos serviços de fisioterapia!"
        try:
            # 1. Abre o Edge e carrega WhatsApp Web
            driver = abrir_whatsapp_web()
            # 2. Mostra o OK somente agora
            self.aguardar_whatsapp_carregar()
            # 3. Só depois do OK faz o envio dos arquivos e mensagem
            self.envio_arquivos_whatsapp(driver, lista_envio, mensagem)
            QMessageBox.information(self, "Envio WhatsApp", "Envio concluído!")
        except Exception as e:
            QMessageBox.warning(self, "Erro no envio WhatsApp", str(e))

    def envio_arquivos_whatsapp(self, driver, lista_envio, mensagem):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import selenium.common.exceptions as se

        for caminho_arquivo, telefone in lista_envio:
            numero = re.sub(r'\D', '', telefone)
            if len(numero) == 10:
                numero = "55" + numero
            elif len(numero) == 11 and not numero.startswith("55"):
                numero = "55" + numero
            elif not numero.startswith("55"):
                numero = "55" + numero[-11:]

            print(f"Enviando para: {numero}")
            driver.get(f"https://web.whatsapp.com/send?phone={numero}&text&app_absent=0")
            time.sleep(10)  # Dê tempo pra conversa abrir

            # Envia mensagem
            if mensagem:
                try:
                    try:
                        msg_box = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@title="Mensagem"]'))
                        )
                    except se.TimeoutException:
                        msg_box = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                        )
                    msg_box.send_keys(mensagem)
                    msg_box.send_keys(Keys.ENTER)
                    time.sleep(2)
                except Exception as e:
                    print("Erro ao enviar mensagem:", e)

            # Envia PDF
            try:
                # Clique no botão de anexo (Attach)
                try:
                    clip_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[title="Attach"]'))
                    )
                    clip_button.click()
                    print("Cliquei no botão Attach (plus)!")
                except Exception as e:
                    print("Erro ao clicar no botão Attach (plus):", e)
                    continue

                time.sleep(2)

                # Espera o input de arquivo aparecer e ser visível
                try:
                    attach_input = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
                    )
                    print("Input de arquivo encontrado!")
                except Exception as e:
                    print("Input de arquivo não apareceu:", e)
                    continue

                attach_input.send_keys(caminho_arquivo)
                print("Arquivo anexado.")
                time.sleep(4)  # Tempo para o WhatsApp fazer upload do PDF

                # Botão de enviar anexo
                try:
                    send_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@role="button"]//span[@data-icon="send"] | //span[@data-icon="send"]'))
                    )
                    send_button.click()
                    print(f"Arquivo enviado para {telefone} ({caminho_arquivo})")
                    time.sleep(5)
                except Exception as e:
                    print("Botão enviar não encontrado:", e)
                    continue

            except Exception as e:
                print(f"Erro ao anexar/enviar PDF para {telefone}: {e}")
                continue

        print("Todos os envios finalizados.")
        driver.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PDFRenomeador()
    win.show()
    sys.exit(app.exec_())
