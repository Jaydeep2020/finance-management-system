# account.py
from abc import ABC, abstractmethod
from collections import namedtuple
from exceptions import InvalidAmountError, InsufficientFundsError
from transaction import Transaction

AccountSummary = namedtuple('AccountSummary', ['account_id', 'account_type', 'balance', 'total_transactions'])

class Account(ABC):
    _total_accounts = 0

    def __init__(self, account_id, initial_balance=0.0, transaction_callback=None):
        self.account_id = account_id
        self.__balance = initial_balance
        self._transactions = []  # list of Transaction objects
        self._transaction_callback = transaction_callback  # function to call after adding a transaction
        Account._total_accounts += 1

    @property
    def balance(self):
        return self.__balance

    @staticmethod
    def validate_amount(amount):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise InvalidAmountError(f"Invalid amount: {amount}. Must be positive.", error_code=1002)

    def _add_transaction(self, transaction):
        """Internal method to add a transaction to history and call the persistence callback."""
        self._transactions.append(transaction)
        if self._transaction_callback:
            self._transaction_callback(transaction, self.account_id)

    def deposit(self, amount, description="Deposit"):
        self.validate_amount(amount)
        self.__balance += amount
        txn = Transaction.create(amount, 'credit', description)
        self._add_transaction(txn)
        return txn

    def withdraw(self, amount, description="Withdrawal"):
        self.validate_amount(amount)
        if amount > self.__balance:
            raise InsufficientFundsError(f"Insufficient balance. Available: {self.__balance}, Requested: {amount}",
                                         error_code=1001)
        self.__balance -= amount
        txn = Transaction.create(amount, 'debit', description)
        self._add_transaction(txn)
        return txn

    def get_statement(self, month=None):
        """Return list of transactions. If month (1-12) is given, filter by that month."""
        if month is None:
            return self._transactions.copy()
        return [txn for txn in self._transactions if txn.timestamp.month == month]

    def get_summary(self):
        return AccountSummary(self.account_id, self.get_account_type(), self.balance, len(self._transactions))

    @abstractmethod
    def apply_monthly_update(self):
        """Apply account-specific monthly logic (interest, fees, EMI). Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_account_type(self) -> str:
        pass

    def __str__(self):
        return f"{self.get_account_type()} Account [{self.account_id}] - Balance: Rs.{self.balance:.2f}"

    def __eq__(self, other):
        if not isinstance(other, Account):
            return False
        return self.account_id == other.account_id