# accounts/loan.py
from account import Account
from transaction import Transaction
from exceptions import UnauthorizedAccessError

class LoanAccount(Account):
    def __init__(self, account_id, principal, emi_amount, remaining_months, transaction_callback=None):
        # For a loan, the outstanding balance is the principal
        super().__init__(account_id, principal, transaction_callback)
        self.principal = principal
        self.emi_amount = emi_amount
        self.remaining_months = remaining_months

    def deposit(self, amount, description="Deposit"):
        # Loan accounts do not accept deposits
        raise UnauthorizedAccessError("Loan accounts do not accept deposits", error_code=2001)

    def apply_monthly_update(self):
        if self.remaining_months <= 0:
            return  # loan fully paid
        # Deduct EMI
        self._add_transaction(Transaction.create(self.emi_amount, 'debit', 'EMI', tags={'emi'}))
        self._Account__balance -= self.emi_amount
        self.remaining_months -= 1

    def get_account_type(self):
        return 'Loan'

    def loan_summary(self):
        return {
            'principal': self.principal,
            'emi': self.emi_amount,
            'months_remaining': self.remaining_months,
            'outstanding': self.balance
        }