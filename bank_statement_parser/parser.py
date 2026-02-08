"""Core parser that reads bank statement files and produces normalized transactions."""

import csv
import os
from datetime import datetime
from typing import List, Optional

from .models import Transaction
from .profiles import get_profile, detect_profile, BankProfile


def parse_amount(value: str) -> Optional[float]:
    """Parse an amount string into a float, handling various formats."""
    if not value or not value.strip():
        return None
    cleaned = value.strip()
    # Remove currency symbols and whitespace
    for ch in ("$", "£", "€", "¥", "\u00a0", ","):
        cleaned = cleaned.replace(ch, "")
    # Handle parentheses as negative: (100.00) -> -100.00
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(value: str, formats: List[str]) -> Optional[datetime]:
    """Try multiple date formats and return the first match."""
    value = value.strip()
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_csv_statement(
    filepath: str,
    profile: Optional[BankProfile] = None,
    account_name: Optional[str] = None,
) -> List[Transaction]:
    """Parse a CSV bank statement file into normalized transactions.

    Args:
        filepath: Path to the CSV file.
        profile: A BankProfile describing the CSV layout. If None, auto-detect.
        account_name: Optional account label to tag transactions with.

    Returns:
        List of Transaction objects.
    """
    filename = os.path.basename(filepath)

    with open(filepath, "r", encoding="utf-8-sig") as f:
        # Read all lines, skip leading blank lines
        lines = f.readlines()

    # Strip BOM and blank leading lines
    while lines and not lines[0].strip():
        lines.pop(0)

    if not lines:
        return []

    # If profile specifies header rows to skip, do so
    skip = 0
    if profile and profile.skip_rows:
        skip = profile.skip_rows

    content_lines = lines[skip:]
    if not content_lines:
        return []

    reader = csv.DictReader(content_lines)
    if reader.fieldnames is None:
        return []

    # Auto-detect profile from headers if not provided
    if profile is None:
        profile = detect_profile(reader.fieldnames)

    if profile is None:
        raise ValueError(
            f"Could not detect bank format for {filepath}. "
            f"Headers found: {reader.fieldnames}. "
            f"Please specify a profile with --profile."
        )

    transactions = []
    for row in reader:
        txn = _row_to_transaction(row, profile, filename, account_name)
        if txn is not None:
            transactions.append(txn)

    return transactions


def _row_to_transaction(
    row: dict,
    profile: BankProfile,
    source_file: str,
    account_name: Optional[str],
) -> Optional[Transaction]:
    """Convert a single CSV row to a Transaction using the bank profile."""
    # Parse date
    date_val = row.get(profile.date_column, "")
    if not date_val or not date_val.strip():
        return None
    parsed_date = parse_date(date_val, profile.date_formats)
    if parsed_date is None:
        return None

    # Parse description
    desc_parts = [row.get(col, "").strip() for col in profile.description_columns]
    description = " - ".join(part for part in desc_parts if part)
    if not description:
        return None

    # Parse amount
    if profile.amount_column:
        # Single amount column (negative = debit, positive = credit)
        raw = row.get(profile.amount_column, "")
        amount = parse_amount(raw)
        if amount is None:
            return None
    elif profile.debit_column and profile.credit_column:
        # Separate debit/credit columns
        debit_raw = row.get(profile.debit_column, "")
        credit_raw = row.get(profile.credit_column, "")
        debit = parse_amount(debit_raw)
        credit = parse_amount(credit_raw)
        if debit is not None and debit != 0:
            amount = -abs(debit)
        elif credit is not None and credit != 0:
            amount = abs(credit)
        else:
            return None
    else:
        return None

    # Parse optional balance
    balance = None
    if profile.balance_column:
        balance = parse_amount(row.get(profile.balance_column, ""))

    # Parse optional reference
    reference = None
    if profile.reference_column:
        reference = row.get(profile.reference_column, "").strip() or None

    # Parse optional category
    category = None
    if profile.category_column:
        category = row.get(profile.category_column, "").strip() or None

    txn_type = "Debit" if amount < 0 else "Credit"

    return Transaction(
        date=parsed_date.date(),
        description=description,
        amount=amount,
        balance=balance,
        category=category,
        transaction_type=txn_type,
        reference=reference,
        source_file=source_file,
        bank=profile.bank_name,
        account=account_name,
    )
