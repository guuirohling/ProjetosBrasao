import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QInputDialog, QMessageBox, QListWidget, QDialog, QDialogButtonBox, QLabel
)
from ofx_parser import parse_ofx
from classifier import classify
from editor import to_dataframe, edit_description, edit_classification
from pdf_exporter import export_to_pdf

class ColumnSelectorDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Colunas para Exportar")
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for col in columns:
            self.list_widget.addItem(col)
        layout.addWidget(QLabel("Selecione as colunas que deseja exportar:"))
        layout.addWidget(self.list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_selected(self):
        return [item.text() for item in self.list_widget.selectedItems()]

class OFXApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Classificador de OFX")
        self.resize(1100, 600)
        self.transactions = []
        self.df = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Carregar OFX")
        self.edit_btn = QPushButton("Editar Selecionado")
        self.export_btn = QPushButton("Exportar para PDF")
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.export_btn)

        self.table = QTableWidget()
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.load_btn.clicked.connect(self.load_ofx)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.export_btn.clicked.connect(self.export_pdf)

        # Atualiza os dados internos quando editar direto na tabela
        self.table.itemChanged.connect(self.update_transaction_from_table)

    def load_ofx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo OFX", "", "OFX Files (*.ofx)")
        if path:
            self.transactions = classify(parse_ofx(path))
            self.df = to_dataframe(self.transactions)
            self.show_table()

    def show_table(self):
        self.table.blockSignals(True)  # Para evitar loop durante update
        self.table.clear()
        if self.df is not None:
            self.table.setRowCount(len(self.df))
            self.table.setColumnCount(len(self.df.columns))
            self.table.setHorizontalHeaderLabels(self.df.columns)
            for i, row in self.df.iterrows():
                for j, col in enumerate(self.df.columns):
                    val = str(row[col])
                    self.table.setItem(i, j, QTableWidgetItem(val))
        self.table.blockSignals(False)

    def edit_selected(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Seleção", "Selecione uma linha!")
            return
        col, ok = QInputDialog.getInt(
            self, "Editar", "Editar coluna (0:Descrição, 1:Classificação):", 0, 0, 1)
        if ok:
            if col == 0:
                text, ok = QInputDialog.getText(
                    self, "Descrição", "Nova descrição:")
                if ok:
                    edit_description(self.transactions, row, text)
            else:
                text, ok = QInputDialog.getText(
                    self, "Classificação", "Nova classificação:")
                if ok:
                    edit_classification(self.transactions, row, text)
            self.df = to_dataframe(self.transactions)
            self.show_table()

    def update_transaction_from_table(self, item):
        row = item.row()
        col = item.column()
        col_name = self.df.columns[col]
        value = item.text()
        # Atualiza tanto o DataFrame quanto self.transactions
        self.df.at[row, col_name] = value
        self.transactions[row][col_name] = value

    def export_pdf(self):
        if self.df is None or self.df.empty:
            QMessageBox.warning(self, "Atenção", "Nenhum dado carregado!")
            return

        # Adiciona a coluna "conta" ANTES da seleção de colunas, se não existir
        if "conta" not in self.df.columns:
            self.df["conta"] = "Banco Inter"

        # Caixa de diálogo para escolher colunas
        dlg = ColumnSelectorDialog(list(self.df.columns), self)
        if not dlg.exec():
            return
        selected_columns = dlg.get_selected()
        if not selected_columns:
            QMessageBox.warning(self, "Atenção", "Nenhuma coluna selecionada!")
            return

        # Força a coluna "amount" (valor) a ser a última, se presente
        if "amount" in selected_columns:
            selected_columns = [col for col in selected_columns if col != "amount"] + ["amount"]

        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar PDF", "", "PDF Files (*.pdf)")
        if path:
            export_df = self.df[selected_columns].copy()
            export_to_pdf(export_df, path)
            QMessageBox.information(
                self, "Exportado", "PDF exportado com sucesso!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = OFXApp()
    win.show()
    sys.exit(app.exec())
