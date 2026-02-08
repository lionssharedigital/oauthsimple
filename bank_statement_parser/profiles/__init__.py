"""Bank profile definitions for different CSV formats."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BankProfile:
    """Describes the CSV layout for a specific bank's statement export."""
    bank_name: str
    date_column: str
    date_formats: List[str]
    description_columns: List[str]

    # Either a single amount column or separate debit/credit columns
    amount_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None

    balance_column: Optional[str] = None
    reference_column: Optional[str] = None
    category_column: Optional[str] = None
    skip_rows: int = 0

    # Headers that identify this profile during auto-detection
    signature_columns: List[str] = field(default_factory=list)


# Registry of known bank profiles
_PROFILES: Dict[str, BankProfile] = {}


def register_profile(name: str, profile: BankProfile) -> None:
    _PROFILES[name.lower()] = profile


def get_profile(name: str) -> Optional[BankProfile]:
    return _PROFILES.get(name.lower())


def list_profiles() -> List[str]:
    return sorted(_PROFILES.keys())


def detect_profile(headers: List[str]) -> Optional[BankProfile]:
    """Try to auto-detect the bank profile from CSV column headers."""
    normalized = [h.strip().lower() for h in headers]
    best_match = None
    best_score = 0

    for profile in _PROFILES.values():
        if not profile.signature_columns:
            continue
        sig = [s.lower() for s in profile.signature_columns]
        matches = sum(1 for s in sig if s in normalized)
        score = matches / len(sig)
        if score > best_score and score >= 0.6:
            best_score = score
            best_match = profile

    return best_match


# Import built-in profiles so they self-register
from . import builtin  # noqa: E402, F401
