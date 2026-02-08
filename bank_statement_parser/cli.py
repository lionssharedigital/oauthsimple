"""Command-line interface for the bank statement parser."""

import argparse
import glob
import os
import sys
from typing import List

from .parser import parse_csv_statement
from .combiner import combine_transactions, compute_summary
from .exporter import export_csv, export_excel
from .profiles import get_profile, list_profiles


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bank-statement-parser",
        description="Parse bank statement CSVs and combine them into a single spreadsheet.",
        epilog="Example: %(prog)s statements/*.csv -o combined.xlsx",
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Bank statement CSV files to parse. Supports glob patterns.",
    )
    parser.add_argument(
        "-o", "--output",
        default="combined_statements.csv",
        help="Output file path. Use .csv or .xlsx extension (default: combined_statements.csv).",
    )
    parser.add_argument(
        "-p", "--profile",
        default=None,
        help="Bank profile to use (e.g., chase, bofa, wellsfargo). Auto-detects if omitted.",
    )
    parser.add_argument(
        "--account",
        default=None,
        help="Account name/label to tag all transactions with.",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable duplicate transaction detection.",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        help="Don't sort transactions by date.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Include a summary section in the output.",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available bank profiles and exit.",
    )

    args = parser.parse_args(argv)

    if args.list_profiles:
        profiles = list_profiles()
        print("Available bank profiles:")
        for name in profiles:
            p = get_profile(name)
            print(f"  {name:20s} - {p.bank_name}")
        return 0

    if not args.files:
        parser.error("the following arguments are required: files")

    # Resolve file paths (expand globs)
    input_files = _resolve_files(args.files)
    if not input_files:
        print("Error: No input files found.", file=sys.stderr)
        return 1

    # Get bank profile if specified
    profile = None
    if args.profile:
        profile = get_profile(args.profile)
        if profile is None:
            print(
                f"Error: Unknown profile '{args.profile}'. "
                f"Use --list-profiles to see available options.",
                file=sys.stderr,
            )
            return 1

    # Parse all files
    all_transactions = []
    for filepath in input_files:
        print(f"Parsing: {filepath}")
        try:
            txns = parse_csv_statement(filepath, profile=profile, account_name=args.account)
            print(f"  -> {len(txns)} transactions found")
            all_transactions.append(txns)
        except Exception as e:
            print(f"  -> Error: {e}", file=sys.stderr)
            continue

    if not all_transactions or all(len(t) == 0 for t in all_transactions):
        print("Error: No transactions were parsed from any file.", file=sys.stderr)
        return 1

    # Combine
    combined = combine_transactions(
        all_transactions,
        deduplicate=not args.no_dedup,
        sort_by_date=not args.no_sort,
    )
    print(f"\nCombined: {len(combined)} transactions")

    # Export
    output_path = args.output
    if output_path.endswith(".xlsx"):
        result_path = export_excel(combined, output_path, include_summary=args.summary)
    else:
        result_path = export_csv(combined, output_path, include_summary=args.summary)

    print(f"Written to: {result_path}")

    # Print summary
    summary = compute_summary(combined)
    print(f"\n--- Summary ---")
    print(f"Transactions: {summary['total_transactions']}")
    print(f"Total Debits: ${abs(summary['total_debits']):,.2f}")
    print(f"Total Credits: ${summary['total_credits']:,.2f}")
    print(f"Net: ${summary['net']:,.2f}")
    if summary["date_range"]:
        print(f"Date Range: {summary['date_range'][0]} to {summary['date_range'][1]}")
    if summary["banks"]:
        print(f"Banks: {', '.join(summary['banks'])}")

    return 0


def _resolve_files(patterns: List[str]) -> List[str]:
    """Expand glob patterns and return a list of existing file paths."""
    files = []
    for pattern in patterns:
        expanded = glob.glob(pattern)
        if expanded:
            files.extend(expanded)
        elif os.path.isfile(pattern):
            files.append(pattern)
    return sorted(set(files))


if __name__ == "__main__":
    sys.exit(main())
