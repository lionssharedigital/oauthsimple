"""Combine and deduplicate transactions from multiple statement files."""

from typing import List

from .models import Transaction


def combine_transactions(
    transaction_lists: List[List[Transaction]],
    deduplicate: bool = True,
    sort_by_date: bool = True,
) -> List[Transaction]:
    """Merge multiple lists of transactions into one, with optional dedup and sort.

    Args:
        transaction_lists: Multiple lists of Transaction objects to merge.
        deduplicate: If True, remove duplicate transactions based on
                     (date, description, amount).
        sort_by_date: If True, sort the final list by date ascending.

    Returns:
        A single merged list of transactions.
    """
    all_txns: List[Transaction] = []
    for txn_list in transaction_lists:
        all_txns.extend(txn_list)

    if deduplicate:
        all_txns = _deduplicate(all_txns)

    if sort_by_date:
        all_txns.sort(key=lambda t: (t.date, t.description))

    return all_txns


def _deduplicate(transactions: List[Transaction]) -> List[Transaction]:
    """Remove duplicate transactions, keeping the first occurrence."""
    seen = {}
    result = []
    for txn in transactions:
        key = txn.dedup_key()
        # Allow same key up to the number of times it appears in a single source file.
        # This handles legitimate duplicate amounts on the same day (e.g., two $5.00 coffees)
        # while still deduplicating across files.
        count = seen.get(key, 0)
        seen[key] = count + 1
        # Keep the transaction if this is the first time we see this key,
        # or if it comes from a different source file than previous ones.
        if count == 0:
            result.append(txn)
        else:
            # Check if all previous occurrences came from the same source file.
            # If this one is from a different file, it's likely a cross-file duplicate.
            prev_sources = [
                t.source_file for t in result if t.dedup_key() == key
            ]
            if txn.source_file not in prev_sources:
                # Same transaction appearing in a different file => skip (duplicate)
                continue
            else:
                # Same file, same key => legitimate repeated transaction
                result.append(txn)

    return result


def compute_summary(transactions: List[Transaction]) -> dict:
    """Compute summary statistics for a list of transactions."""
    if not transactions:
        return {
            "total_transactions": 0,
            "total_debits": 0.0,
            "total_credits": 0.0,
            "net": 0.0,
            "date_range": None,
            "banks": [],
            "source_files": [],
        }

    debits = sum(t.amount for t in transactions if t.is_debit)
    credits = sum(t.amount for t in transactions if t.is_credit)
    banks = sorted(set(t.bank for t in transactions if t.bank))
    sources = sorted(set(t.source_file for t in transactions if t.source_file))
    dates = [t.date for t in transactions]

    return {
        "total_transactions": len(transactions),
        "total_debits": round(debits, 2),
        "total_credits": round(credits, 2),
        "net": round(debits + credits, 2),
        "date_range": (min(dates).isoformat(), max(dates).isoformat()),
        "banks": banks,
        "source_files": sources,
    }
