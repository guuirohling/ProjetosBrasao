from ofxparse import OfxParser

def parse_ofx(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        ofx = OfxParser.parse(f)
    transactions = []
    for acc in ofx.accounts:
        for txn in acc.statement.transactions:
            transactions.append({
                'date': txn.date,
                'amount': txn.amount,
                'payee': txn.payee,
                'memo': txn.memo,
                'type': 'IN' if txn.amount > 0 else 'OUT',
                'classification': '',
                'description': txn.memo or txn.payee
            })
    return transactions
