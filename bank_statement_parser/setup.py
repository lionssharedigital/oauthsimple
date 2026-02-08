"""Setup script for bank_statement_parser."""

from setuptools import setup, find_packages

setup(
    name="bank-statement-parser",
    version="1.0.0",
    description="Parse bank statement CSVs and combine them into a single spreadsheet",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "openpyxl>=3.0",
    ],
    entry_points={
        "console_scripts": [
            "bank-statement-parser=bank_statement_parser.cli:main",
        ],
    },
)
