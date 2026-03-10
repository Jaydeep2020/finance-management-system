# user.py
import uuid
from exceptions import AccountNotFoundError

class User:
    def __init__(self, name, email=None, user_id=None):
        self.user_id = user_id if user_id else str(uuid.uuid4())[:8]
        self.name = name
        self.email = email
        self.__accounts = {}  # account_id -> Account

    def add_account(self, account):
        if account.account_id in self.__accounts:
            raise ValueError(f"Account {account.account_id} already exists for this user.")
        self.__accounts[account.account_id] = account

    def get_account(self, account_id):
        if account_id not in self.__accounts:
            raise AccountNotFoundError(f"Account {account_id} not found.", error_code=3001)
        return self.__accounts[account_id]

    def remove_account(self, account_id):
        if account_id not in self.__accounts:
            raise AccountNotFoundError(f"Account {account_id} not found.", error_code=3001)
        del self.__accounts[account_id]

    def total_balance(self):
        """Sum of balances of non-loan accounts."""
        return sum(acc.balance for acc in self.__accounts.values() if acc.get_account_type() != 'Loan')

    def net_worth(self):
        """Total balance minus loan outstanding."""
        loans_outstanding = sum(acc.balance for acc in self.__accounts.values() if acc.get_account_type() == 'Loan')
        return self.total_balance() - loans_outstanding

    def get_all_summaries(self):
        return [acc.get_summary() for acc in self.__accounts.values()]

    def apply_all_monthly_updates(self):
        """Call apply_monthly_update on all accounts. Return list of exceptions encountered."""
        errors = []
        for acc in self.__accounts.values():
            try:
                acc.apply_monthly_update()
            except Exception as e:
                errors.append((acc.account_id, e))
        return errors

    def list_accounts(self):
        return list(self.__accounts.values())