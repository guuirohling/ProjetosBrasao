import sys
import os
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QHBoxLayout, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyPDF2 import PdfReader

def extract_tomador_nome(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        # Busca o bloco de TOMADOR DE SERVIÇOS
        bloco = re.search(r'TOMADOR DE SERVIÇOS(.*?)(?:DISCRIMINAÇÃO DOS SERVIÇOS|VALOR TOTAL DA NFS-e)', text, re.DOTALL | re.IGNORECASE)
        if bloco:
            linhas = [linha.strip() for linha in bloco.group(1).split('\n') if linha.strip()]
            for i, linha in enumerate(linhas):
                # Procura um CPF (padrão 000.000.000-00)
                if re.match(r'\d{3}\.\d{3}\.\d{3}-\d{2}', linha):
                    if i+1 < len(linhas):
                        nome = linhas[i+1]
                        nome = re.sub(r'[\\/:*?"<>|]', '', nome)
                        return nome
    except Exception as e:
        print(f"Erro ao ler {pdf_path}: {e}")
    return "Nao Encontrado"

class PDFRenomeador(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Renomeador de PDFs NFS-e")
        self.resize(900, 400)
        self.pdf_list = []
        self.destino = ""

        layout = QVBoxLayout()

        # Botões
        btn_layout = QHBoxLayout()
        self.btn_importar = QPushButton("Importar PDFs")
        self.btn_destino = QPushButton("Selecionar pasta destino")
        self.btn_processar = QPushButton("Processar")
        btn_layout.addWidget(self.btn_importar)
        btn_layout.addWidget(self.btn_destino)
        btn_layout.addWidget(self.btn_processar)

        # Tabela
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Selecionar", "Nome Original", "Nome Sugerido", "Editar Nome Final"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # Eventos
        self.btn_importar.clicked.connect(self.importar_pdfs)
        self.btn_destino.clicked.connect(self.selecionar_destino)
        self.btn_processar.clicked.connect(self.processar)

    def importar_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF Files (*.pdf)")
        for file in files:
            if file not in [row[0] for row in self.pdf_list]:
                nome_tomador = extract_tomador_nome(file)
                nome_sugerido = f"NF - {nome_tomador}.pdf"
                self.pdf_list.append([file, os.path.basename(file), nome_sugerido, nome_sugerido, True])
        self.atualiza_tabela()

    def atualiza_tabela(self):
        self.table.blockSignals(True)  # Evita triggers desnecessários
        self.table.setRowCount(0)
        for row_idx, (filepath, nome_original, nome_sugerido, nome_final, selecionado) in enumerate(self.pdf_list):
            self.table.insertRow(row_idx)
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(selecionado)
            checkbox.stateChanged.connect(lambda state, idx=row_idx: self.checkbox_changed(idx, state))
            self.table.setCellWidget(row_idx, 0, checkbox)
            # Nome original
            item_nome_ori = QTableWidgetItem(nome_original)
            item_nome_ori.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 1, item_nome_ori)
            # Nome sugerido
            item_nome_sug = QTableWidgetItem(nome_sugerido)
            item_nome_sug.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 2, item_nome_sug)
            # Editar nome final
            item_nome_final = QTableWidgetItem(nome_final)
            self.table.setItem(row_idx, 3, item_nome_final)
        self.table.blockSignals(False)
        self.table.cellChanged.connect(self.nome_final_editado)

    def checkbox_changed(self, idx, state):
        self.pdf_list[idx][4] = bool(state)

    def nome_final_editado(self, row, column):
        if column == 3:
            novo_nome = self.table.item(row, 3).text()
            self.pdf_list[row][3] = novo_nome

    def selecionar_destino(self):
        destino = QFileDialog.getExistingDirectory(self, "Selecionar pasta destino")
        if destino:
            self.destino = destino

    def processar(self):
        if not self.destino:
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta destino!")
            return
        processados = 0
        for filepath, _, _, nome_final, selecionado in self.pdf_list:
            if selecionado:
                novo_caminho = os.path.join(self.destino, nome_final)
                try:
                    with open(filepath, "rb") as src, open(novo_caminho, "wb") as dst:
                        dst.write(src.read())
                    processados += 1
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Erro ao processar {filepath}: {e}")
        QMessageBox.information(self, "Processamento finalizado", f"{processados} arquivos processados!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PDFRenomeador()
    win.show()
    sys.exit(app.exec_())
