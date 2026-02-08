"""Built-in bank profiles for common statement formats."""

from . import BankProfile, register_profile

# ── Chase ────────────────────────────────────────────────────────────────────
register_profile("chase", BankProfile(
    bank_name="Chase",
    date_column="Posting Date",
    date_formats=["%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Description"],
    amount_column="Amount",
    balance_column="Balance",
    category_column="Type",
    signature_columns=["Posting Date", "Description", "Amount", "Type", "Balance"],
))

register_profile("chase_credit", BankProfile(
    bank_name="Chase Credit Card",
    date_column="Transaction Date",
    date_formats=["%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Description"],
    amount_column="Amount",
    category_column="Category",
    reference_column="Post Date",
    signature_columns=["Transaction Date", "Post Date", "Description", "Category", "Amount"],
))

# ── Bank of America ──────────────────────────────────────────────────────────
register_profile("bofa", BankProfile(
    bank_name="Bank of America",
    date_column="Date",
    date_formats=["%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Description"],
    amount_column="Amount",
    balance_column="Running Bal.",
    signature_columns=["Date", "Description", "Amount", "Running Bal."],
))

# ── Wells Fargo ──────────────────────────────────────────────────────────────
register_profile("wellsfargo", BankProfile(
    bank_name="Wells Fargo",
    date_column="Date",
    date_formats=["%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Description"],
    amount_column="Amount",
    signature_columns=["Date", "Description", "Amount"],
))

# ── Capital One ──────────────────────────────────────────────────────────────
register_profile("capitalone", BankProfile(
    bank_name="Capital One",
    date_column="Transaction Date",
    date_formats=["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Transaction Description"],
    debit_column="Debit",
    credit_column="Credit",
    balance_column="Balance",
    category_column="Category",
    signature_columns=["Transaction Date", "Transaction Description", "Debit", "Credit", "Balance"],
))

# ── Citi ─────────────────────────────────────────────────────────────────────
register_profile("citi", BankProfile(
    bank_name="Citi",
    date_column="Date",
    date_formats=["%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Description"],
    debit_column="Debit",
    credit_column="Credit",
    signature_columns=["Date", "Description", "Debit", "Credit"],
))

# ── US Bank ──────────────────────────────────────────────────────────────────
register_profile("usbank", BankProfile(
    bank_name="US Bank",
    date_column="Date",
    date_formats=["%Y-%m-%d", "%m/%d/%Y"],
    description_columns=["Name"],
    amount_column="Amount",
    reference_column="Transaction",
    signature_columns=["Date", "Transaction", "Name", "Memo", "Amount"],
))

# ── PNC ──────────────────────────────────────────────────────────────────────
register_profile("pnc", BankProfile(
    bank_name="PNC",
    date_column="Date",
    date_formats=["%m/%d/%Y", "%Y-%m-%d"],
    description_columns=["Description"],
    debit_column="Withdrawals",
    credit_column="Deposits",
    balance_column="Balance",
    reference_column="Reference Number",
    signature_columns=["Date", "Description", "Withdrawals", "Deposits", "Balance"],
))

# ── TD Bank ──────────────────────────────────────────────────────────────────
register_profile("td", BankProfile(
    bank_name="TD Bank",
    date_column="Date",
    date_formats=["%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Description"],
    debit_column="Debit",
    credit_column="Credit",
    balance_column="Balance",
    signature_columns=["Date", "Description", "Debit", "Credit", "Balance"],
))

# ── Generic / Mint export ────────────────────────────────────────────────────
register_profile("mint", BankProfile(
    bank_name="Mint Export",
    date_column="Date",
    date_formats=["%m/%d/%Y", "%m/%d/%y"],
    description_columns=["Original Description"],
    amount_column="Amount",
    category_column="Category",
    signature_columns=["Date", "Original Description", "Amount", "Transaction Type", "Category", "Account Name"],
))

# ── Generic CSV (common column names) ────────────────────────────────────────
register_profile("generic", BankProfile(
    bank_name="Generic",
    date_column="Date",
    date_formats=["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%Y/%m/%d"],
    description_columns=["Description"],
    amount_column="Amount",
    balance_column="Balance",
    signature_columns=["Date", "Description", "Amount"],
))
