import pandas as pd

def edit_description(transactions, index, new_description):
    transactions[index]['description'] = new_description
    return transactions

def edit_classification(transactions, index, new_classification):
    transactions[index]['classification'] = new_classification
    return transactions

def to_dataframe(transactions):
    return pd.DataFrame(transactions)
