# transaction.py
import uuid
from datetime import datetime

class Transaction:
    _id_counter = 0

    def __init__(self, amount, t_type, description, tags=None, timestamp=None, transaction_id=None):
        """
        :param amount: float
        :param t_type: 'credit' or 'debit'
        :param description: str
        :param tags: set of strings
        :param timestamp: datetime object (if None, set to now)
        :param transaction_id: str (if None, auto-generate)
        """
        self.amount = amount
        self.type = t_type  # 'credit' or 'debit'
        self.description = description
        self.tags = set(tags) if tags else set()

        if timestamp is None:
            self.timestamp = datetime.now()
        else:
            self.timestamp = timestamp

        if transaction_id is None:
            Transaction._id_counter += 1
            self.transaction_id = f"TXN{Transaction._id_counter:06d}"
        else:
            self.transaction_id = transaction_id

    @staticmethod
    def from_string(data: str):
        """
        Parses a CSV line: "amount,type,description,tags[,timestamp]"
        Example: "500,credit,salary,tag1|tag2,2025-03-09 10:30:00"
        If timestamp is omitted, current time is used.
        """
        parts = data.strip().split(',')
        if len(parts) < 4:
            raise ValueError("Invalid transaction string format")

        # amount = float(parts[0])
        # t_type = parts[1]
        # description = parts[2]
        # tags_str = parts[3]
        # tags = tags_str.split('|') if tags_str else []

        # timestamp = None
        # if len(parts) >= 5:
        #     timestamp = datetime.strptime(parts[4], "%Y-%m-%d %H:%M:%S")

        # return Transaction(amount, t_type, description, tags, timestamp)

        transaction_id = parts[0]
        amount = float(parts[1])
        t_type = parts[2]
        description = parts[3]

        tags_str = parts[4]
        tags = tags_str.split('|') if tags_str else []

        timestamp = datetime.strptime(parts[5], "%Y-%m-%d %H:%M:%S")

        return Transaction(amount, t_type, description, tags, timestamp, transaction_id)

    @classmethod
    def create(cls, amount, t_type, description, tags=None):
        """Factory method that auto-generates ID and timestamp."""
        return cls(amount, t_type, description, tags)

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'type': self.type,
            'description': self.description,
            'tags': list(self.tags),
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __str__(self):
        return (f"Transaction[{self.transaction_id}] {self.type.upper()} "
                f"Rs.{self.amount:.2f} - {self.description} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})")

    def __repr__(self):
        return f"Transaction('{self.transaction_id}', {self.amount}, '{self.type}', '{self.description}')"