# main.py
import sys
from user import User
from accounts.savings import SavingsAccount
from accounts.current import CurrentAccount
from accounts.loan import LoanAccount
from transaction import Transaction
import utils
from exceptions import *
import uuid

def print_header(title):
    print("\n" + "=" * 60)
    print(f"{title:^60}")
    print("=" * 60)

def get_float_input(prompt, allow_zero=False):
    while True:
        try:
            val = float(input(prompt))
            if val <= 0 and not allow_zero:
                print("Please enter a positive number.")
                continue
            return val
        except ValueError:
            print("Invalid number. Try again.")

def get_int_input(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = int(input(prompt))
            if min_val is not None and val < min_val:
                print(f"Please enter at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"Please enter at most {max_val}.")
                continue
            return val
        except ValueError:
            print("Invalid integer. Try again.")

def setup_new_user():
    """Interactive user and account creation."""
    print_header("WELCOME TO PERSONAL FINANCE MANAGER")
    name = input("Enter your name: ").strip()
    if not name:
        name = "Default User"
    user = User(name)

    print("\nLet's set up your accounts.")

    # Savings Account
    if input("Create a Savings Account? (y/n): ").lower().startswith('y'):
        initial = get_float_input("Initial deposit amount: ")
        rate = get_float_input("Interest rate (e.g., 4.5 for 4.5%): ")
        acc_id = str(uuid.uuid4())[:8]
        # Use a callback that saves each transaction to CSV
        def callback(txn, acc_id):
            utils.save_transaction(txn, acc_id)
        acc = SavingsAccount(acc_id, rate, initial, transaction_callback=callback)
        user.add_account(acc)
        # Create initial deposit transaction
        txn = acc.deposit(initial, "Initial deposit")
        utils.save_transaction(txn, acc_id)  # callback already does this, but we call explicitly to ensure saving
        print(f"Savings account {acc_id} created with Rs.{initial:.2f}.")

    # Current Account
    if input("\nCreate a Current Account? (y/n): ").lower().startswith('y'):
        initial = get_float_input("Initial deposit amount: ")
        monthly_fee = get_float_input("Monthly fee: ")
        overdraft = get_float_input("Overdraft limit: ")
        acc_id = str(uuid.uuid4())[:8]
        def callback(txn, acc_id):
            utils.save_transaction(txn, acc_id)
        acc = CurrentAccount(acc_id, monthly_fee, overdraft, initial, transaction_callback=callback)
        user.add_account(acc)
        txn = acc.deposit(initial, "Initial deposit")
        utils.save_transaction(txn, acc_id)
        print(f"Current account {acc_id} created with Rs.{initial:.2f}.")

    # Loan Account
    if input("\nCreate a Loan Account? (y/n): ").lower().startswith('y'):
        principal = get_float_input("Loan principal amount: ")
        emi = get_float_input("Monthly EMI amount: ")
        months = get_int_input("Remaining months: ", min_val=1)
        acc_id = str(uuid.uuid4())[:8]
        def callback(txn, acc_id):
            utils.save_transaction(txn, acc_id)
        # For loan, the initial balance is the principal. We'll create a credit transaction for disbursement.
        acc = LoanAccount(acc_id, principal, emi, months, transaction_callback=callback)
        user.add_account(acc)
        # Record loan disbursement as a credit transaction
        txn = Transaction.create(principal, 'credit', 'Loan disbursement')
        acc._add_transaction(txn)
        acc._Account__balance = principal  # already set by constructor, but ensure
        utils.save_transaction(txn, acc_id)
        print(f"Loan account {acc_id} created with principal Rs.{principal:.2f}.")

    utils.save_user_data(user)
    print("\nSetup complete! Your data has been saved.")
    return user

def load_existing_user():
    """Load user and accounts from JSON, then replay transactions."""
    user, accounts_dict = utils.load_user_data()
    if user is None:
        return None
    # Replay transactions into history
    utils.load_all_transactions(accounts_dict)
    print(f"Welcome back, {user.name}!")
    return user

def main():
    # Try to load existing user, otherwise set up new one
    user = load_existing_user()
    if user is None:
        user = setup_new_user()

    # Main menu loop
    while True:
        print_header("MAIN MENU")
        print("1. View all accounts")
        print("2. Deposit to account")
        print("3. Withdraw from account")
        print("4. View account statement (with optional month filter)")
        print("5. Apply monthly updates to all accounts")
        print("6. View full financial report")
        print("7. Exit")
        choice = input("Enter your choice (1-7): ").strip()

        try:
            if choice == '1':
                # View all accounts
                if not user.list_accounts():
                    print("No accounts found.")
                else:
                    for acc in user.list_accounts():
                        print(acc)

            elif choice == '2':
                # Deposit
                acc_id = input("Enter account ID: ").strip()
                acc = user.get_account(acc_id)
                amount = get_float_input("Amount to deposit: ")
                desc = input("Description (optional): ") or "Deposit"
                txn = acc.deposit(amount, desc)
                utils.save_transaction(txn, acc_id)
                utils.save_user_data(user)
                print(f"Deposit successful. New balance: {utils.format_currency(acc.balance)}")

            elif choice == '3':
                # Withdraw
                acc_id = input("Enter account ID: ").strip()
                acc = user.get_account(acc_id)
                amount = get_float_input("Amount to withdraw: ")
                desc = input("Description (optional): ") or "Withdrawal"
                txn = acc.withdraw(amount, desc)
                utils.save_transaction(txn, acc_id)
                utils.save_user_data(user)
                print(f"Withdrawal successful. New balance: {utils.format_currency(acc.balance)}")

            elif choice == '4':
                # Statement
                acc_id = input("Enter account ID: ").strip()
                acc = user.get_account(acc_id)
                month_input = input("Filter by month (1-12, or leave blank for all): ").strip()
                month = int(month_input) if month_input else None
                stmt = acc.get_statement(month)
                if not stmt:
                    print("No transactions found.")
                else:
                    print(f"\nStatement for {acc.get_account_type()} Account [{acc_id}]")
                    for txn in stmt:
                        print(f"  {txn}")

            elif choice == '5':
                # Apply monthly updates
                errors = user.apply_all_monthly_updates()
                # Save any transactions that were added during updates
                for acc in user.list_accounts():
                    # We need to capture the newly added transactions.
                    # Since apply_monthly_update already added them to history,
                    # we can assume the last transaction(s) of the month are the new ones.
                    # For simplicity, we'll just save all transactions of the account? 
                    # But that would duplicate. Better: after updates, we can scan for transactions with today's date.
                    # However, for this demo, we'll assume updates are applied only once per session.
                    # We'll just save all transactions that have timestamp within the last minute.
                    from datetime import datetime, timedelta
                    now = datetime.now()
                    for txn in acc.get_statement():
                        if now - txn.timestamp < timedelta(minutes=1):
                            utils.save_transaction(txn, acc.account_id)
                utils.save_user_data(user)
                print("Monthly updates applied.")
                if errors:
                    print("Errors encountered:")
                    for acc_id, err in errors:
                        print(f"  Account {acc_id}: {err}")

            elif choice == '6':
                # Full report
                report = utils.generate_report(user)
                print_header("FINANCIAL REPORT")
                print(f"User: {report['user_name']}")
                print(f"Total Balance (non-loan): {utils.format_currency(report['total_balance'])}")
                print(f"Net Worth: {utils.format_currency(report['net_worth'])}")
                print("\n--- Account Summaries ---")
                for summ in report['account_summaries']:
                    print(f"{summ['account_type']} {summ['account_id']}: "
                          f"Balance {utils.format_currency(summ['balance'])}, "
                          f"Transactions: {summ['total_transactions']}")
                print("\n--- Top 5 Recent Transactions ---")
                for txn_dict in report['top_5_transactions']:
                    print(f"  {txn_dict['timestamp']} | {txn_dict['type'].upper()} | "
                          f"{utils.format_currency(txn_dict['amount'])} | {txn_dict['description']}")

            elif choice == '7':
                print("Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter 1-7.")

        except AccountNotFoundError as e:
            print(f"Error: {e}")
        except InsufficientFundsError as e:
            print(f"Error: {e}")
        except InvalidAmountError as e:
            print(f"Error: {e}")
        except UnauthorizedAccessError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()