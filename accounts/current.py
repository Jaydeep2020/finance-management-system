# accounts/current.py
from account import Account
from transaction import Transaction
from exceptions import InsufficientFundsError

class CurrentAccount(Account):
    def __init__(self, account_id, monthly_fee, overdraft_limit, initial_balance=0.0, transaction_callback=None):
        super().__init__(account_id, initial_balance, transaction_callback)
        self.monthly_fee = monthly_fee
        self.overdraft_limit = overdraft_limit

    def apply_monthly_update(self):
        # Deduct monthly fee even if it causes negative balance (overdraft)
        self._add_transaction(Transaction.create(self.monthly_fee, 'debit', 'Monthly fee', tags={'fee'}))
        self._Account__balance -= self.monthly_fee

    def get_account_type(self):
        return 'Current'

    def withdraw(self, amount, description="Withdrawal"):
        self.validate_amount(amount)
        # Allowed to go negative up to overdraft_limit
        if self.balance - amount < -self.overdraft_limit:
            raise InsufficientFundsError(
                f"Withdrawal would exceed overdraft limit of Rs.{self.overdraft_limit}. "
                f"Current balance: Rs.{self.balance}",
                error_code=1004)
        self._Account__balance -= amount
        txn = Transaction.create(amount, 'debit', description)
        self._add_transaction(txn)
        return txn