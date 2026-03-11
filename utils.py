# utils.py
import csv
import json
import os
from datetime import datetime
from user import User
from transaction import Transaction
from accounts.savings import SavingsAccount
from accounts.current import CurrentAccount
from accounts.loan import LoanAccount
from exceptions import AccountNotFoundError

DATA_DIR = "data"
USER_DATA_FILE = os.path.join(DATA_DIR, "user_data.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.csv")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

# ---------- Filtering and Reporting ----------
def filter_transactions(transactions, **kwargs):
    """
    Filter a list of transactions.
    Supported kwargs: type='credit'/'debit', min_amount=float, max_amount=float,
                      tag='tag', start_date=datetime, end_date=datetime.
    """
    filtered = transactions[:]
    if 'type' in kwargs:
        filtered = [t for t in filtered if t.type == kwargs['type']]
    if 'min_amount' in kwargs:
        filtered = [t for t in filtered if t.amount >= kwargs['min_amount']]
    if 'max_amount' in kwargs:
        filtered = [t for t in filtered if t.amount <= kwargs['max_amount']]
    if 'tag' in kwargs:
        filtered = [t for t in filtered if kwargs['tag'] in t.tags]
    if 'start_date' in kwargs:
        filtered = [t for t in filtered if t.timestamp >= kwargs['start_date']]
    if 'end_date' in kwargs:
        filtered = [t for t in filtered if t.timestamp <= kwargs['end_date']]
    return filtered

def generate_report(user):
    """Return comprehensive dict with user's financial data."""
    all_transactions = []
    for acc in user.list_accounts():
        all_transactions.extend(acc.get_statement())
    all_transactions.sort(key=lambda t: t.timestamp, reverse=True)
    top_5 = all_transactions[:5]

    return {
        'user_name': user.name,
        'total_balance': user.total_balance(),
        'net_worth': user.net_worth(),
        'account_summaries': [s._asdict() for s in user.get_all_summaries()],
        'top_5_transactions': [t.to_dict() for t in top_5]
    }

# ---------- Currency Formatting ----------
def format_currency(amount):
    """Indian currency format: Rs. 1,23,456.78"""
    s = f"{amount:.2f}"
    parts = s.split('.')
    integer_part = parts[0]
    fractional_part = parts[1]
    # Indian numbering: last 3 digits then commas every 2
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        # group rest in pairs from right
        rest_groups = []
        while rest:
            rest_groups.append(rest[-2:])
            rest = rest[:-2]
        rest_groups.reverse()
        integer_part = ','.join(rest_groups + [last_three])
    return f"Rs. {integer_part}.{fractional_part}"

# ---------- Persistence ----------
def save_user_data(user):
    """Save user and account details (without transactions) to JSON."""
    ensure_data_dir()
    data = {
        'user_id': user.user_id,
        'name': user.name,
        'email': user.email,
        'accounts': []
    }
    for acc in user.list_accounts():
        acc_data = {
            'account_id': acc.account_id,
            'type': acc.get_account_type(),
            'balance': acc.balance,  # for quick restore
        }
        if isinstance(acc, SavingsAccount):
            acc_data['interest_rate'] = acc.interest_rate
        elif isinstance(acc, CurrentAccount):
            acc_data['monthly_fee'] = acc.monthly_fee
            acc_data['overdraft_limit'] = acc.overdraft_limit
        elif isinstance(acc, LoanAccount):
            acc_data['principal'] = acc.principal
            acc_data['emi_amount'] = acc.emi_amount
            acc_data['remaining_months'] = acc.remaining_months
        data['accounts'].append(acc_data)

    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_user_data():
    """Load user and accounts from JSON. Returns (user, accounts_dict) or (None, None) if file missing."""
    if not os.path.exists(USER_DATA_FILE):
        return None, None
    with open(USER_DATA_FILE, 'r') as f:
        data = json.load(f)

    user = User(data['name'], data.get('email'), data['user_id'])
    accounts = {}
    for acc_data in data['accounts']:
        acc_id = acc_data['account_id']
        acc_type = acc_data['type']
        balance = acc_data['balance']
        if acc_type == 'Savings':
            acc = SavingsAccount(acc_id, acc_data['interest_rate'], balance)
        elif acc_type == 'Current':
            acc = CurrentAccount(acc_id, acc_data['monthly_fee'], acc_data['overdraft_limit'], balance)
        elif acc_type == 'Loan':
            acc = LoanAccount(acc_id, acc_data['principal'], acc_data['emi_amount'], acc_data['remaining_months'])
            # Override balance (may have changed due to EMI)
            acc._Account__balance = balance
        else:
            continue
        user.add_account(acc)
        accounts[acc_id] = acc
    return user, accounts

# def save_transaction(transaction, account_id):
#     """Append a single transaction to the CSV file."""
#     ensure_data_dir()
#     file_exists = os.path.isfile(TRANSACTIONS_FILE)
#     with open(TRANSACTIONS_FILE, 'a', newline='') as f:
#         writer = csv.writer(f)
#         if not file_exists:
#             writer.writerow(['account_id', 'amount', 'type', 'description', 'tags', 'timestamp'])
#         writer.writerow([
#             account_id,
#             transaction.amount,
#             transaction.type,
#             transaction.description,
#             '|'.join(transaction.tags),
#             transaction.timestamp.strftime("%Y-%m-%d %H:%M:%S")
#         ])

def save_transaction(transaction, account_id):
    """Append a single transaction to the CSV file."""
    ensure_data_dir()
    file_exists = os.path.isfile(TRANSACTIONS_FILE)

    with open(TRANSACTIONS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)

        # Write header if file does not exist
        if not file_exists:
            writer.writerow([
                'transaction_id',
                'account_id',
                'amount',
                'type',
                'description',
                'tags',
                'timestamp'
            ])

        # Write transaction data
        writer.writerow([
            transaction.transaction_id,   # ✅ added
            account_id,
            transaction.amount,
            transaction.type,
            transaction.description,
            '|'.join(transaction.tags),
            transaction.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ])

def load_all_transactions(accounts_dict):
    """Read transactions.csv and replay each transaction into the corresponding account.
       This populates each account's _transactions list without modifying balance again.
    """
    if not os.path.exists(TRANSACTIONS_FILE):
        return

    with open(TRANSACTIONS_FILE, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            acc_id = row['account_id']

            if acc_id not in accounts_dict:
                continue  # skip orphaned transactions

            account = accounts_dict[acc_id]

            # Safely parse tags
            tags = row['tags'].split('|') if row['tags'] else []

            # Recreate Transaction object
            txn = Transaction(
                amount=float(row['amount']),
                t_type=row['type'],
                description=row['description'],
                tags=tags,
                timestamp=datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S"),
                transaction_id=row['transaction_id']
            )

            # Update ID counter to avoid duplicates
            num = int(row['transaction_id'].replace("TXN", ""))
            if num > Transaction._id_counter:
                Transaction._id_counter = num

            # Add transaction to account history
            account._transactions.append(txn)

# def load_all_transactions(accounts_dict):
#     """Read transactions.csv and replay each transaction into the corresponding account.
#        This populates each account's _transactions list and updates balance to match JSON (we trust JSON balance).
#        But we still add transactions to history without modifying balance again.
#     """
#     if not os.path.exists(TRANSACTIONS_FILE):
#         return
#     with open(TRANSACTIONS_FILE, 'r') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             acc_id = row['account_id']
#             if acc_id not in accounts_dict:
#                 continue  # skip orphaned transactions
#             account = accounts_dict[acc_id]
#             # Recreate transaction
#             txn = Transaction(
#                 amount=float(row['amount']),
#                 t_type=row['type'],
#                 description=row['description'],
#                 tags=row['tags'].split('|') if row['tags'] else [],
#                 timestamp=datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
#             )
#             # Add to history without changing balance (balance already set from JSON)
#             account._transactions.append(txn)