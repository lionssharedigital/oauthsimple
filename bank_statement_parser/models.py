"""Data models for normalized transactions."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Transaction:
    """A single normalized bank transaction."""
    date: date
    description: str
    amount: float
    balance: Optional[float] = None
    category: Optional[str] = None
    transaction_type: Optional[str] = None  # debit / credit
    reference: Optional[str] = None
    source_file: Optional[str] = None
    bank: Optional[str] = None
    account: Optional[str] = None

    @property
    def is_debit(self) -> bool:
        return self.amount < 0

    @property
    def is_credit(self) -> bool:
        return self.amount > 0

    def to_dict(self) -> dict:
        return {
            "Date": self.date.isoformat(),
            "Description": self.description,
            "Amount": self.amount,
            "Type": self.transaction_type or ("Debit" if self.is_debit else "Credit"),
            "Balance": self.balance,
            "Category": self.category or "",
            "Reference": self.reference or "",
            "Bank": self.bank or "",
            "Account": self.account or "",
            "Source File": self.source_file or "",
        }

    def dedup_key(self) -> tuple:
        """Key used for deduplication."""
        return (self.date, self.description.strip().lower(), self.amount)
