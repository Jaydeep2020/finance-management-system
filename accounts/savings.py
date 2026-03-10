# accounts/savings.py
from account import Account
from transaction import Transaction
from exceptions import InsufficientFundsError

class SavingsAccount(Account):
    MINIMUM_BALANCE = 1000.0

    def __init__(self, account_id, interest_rate, initial_balance=0.0, transaction_callback=None):
        super().__init__(account_id, initial_balance, transaction_callback)
        self.interest_rate = interest_rate  # e.g., 4.5 for 4.5%

    def apply_monthly_update(self):
        interest = self.balance * self.interest_rate / 12 / 100
        if interest > 0:
            self._add_transaction(Transaction.create(interest, 'credit', 'Monthly interest', tags={'interest'}))
            # Directly update balance (using private attribute to avoid extra callback)
            self._Account__balance += interest

    def get_account_type(self):
        return 'Savings'

    def withdraw(self, amount, description="Withdrawal"):
        # Check minimum balance condition
        if self.balance - amount < self.MINIMUM_BALANCE:
            raise InsufficientFundsError(
                f"Cannot withdraw Rs.{amount}. Minimum balance of Rs.{self.MINIMUM_BALANCE} must be maintained.",
                error_code=1003)
        return super().withdraw(amount, description)