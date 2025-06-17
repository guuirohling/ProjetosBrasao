import os
import xml.etree.ElementTree as ET

# Processa todos arquivos .xml da pasta atual
for file in os.listdir('.'):
    if file.lower().endswith('.xml'):
        tree = ET.parse(file)
        root = tree.getroot()
        contas = root.find('.//contas')
        if contas is not None:
            contas_validas = []
            for conta in contas.findall('conta'):
                debito = conta.findtext('debito')
                credito = conta.findtext('credito')
                saldo = conta.findtext('saldo')
                if not (debito == '0,00' and credito == '0,00' and saldo == '0,00'):
                    contas_validas.append(conta)
            # Limpa e repopula
            contas.clear()
            for c in contas_validas:
                contas.append(c)
            tree.write(file, encoding='iso-8859-1', xml_declaration=True)
