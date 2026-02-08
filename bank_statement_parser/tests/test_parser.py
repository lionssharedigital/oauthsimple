"""Tests for the bank statement parser."""

import csv
import os
import tempfile
import unittest
from datetime import date

from bank_statement_parser.parser import parse_csv_statement, parse_amount, parse_date
from bank_statement_parser.combiner import combine_transactions, compute_summary
from bank_statement_parser.exporter import export_csv
from bank_statement_parser.profiles import get_profile, detect_profile, list_profiles
from bank_statement_parser.models import Transaction


class TestParseAmount(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_amount("100.00"), 100.00)

    def test_negative(self):
        self.assertEqual(parse_amount("-50.25"), -50.25)

    def test_currency_symbol(self):
        self.assertEqual(parse_amount("$1,234.56"), 1234.56)

    def test_parentheses_negative(self):
        self.assertEqual(parse_amount("(100.00)"), -100.00)

    def test_empty(self):
        self.assertIsNone(parse_amount(""))

    def test_none_string(self):
        self.assertIsNone(parse_amount("   "))

    def test_euro(self):
        self.assertEqual(parse_amount("€500.00"), 500.00)


class TestParseDate(unittest.TestCase):
    def test_us_format(self):
        result = parse_date("01/15/2024", ["%m/%d/%Y"])
        self.assertIsNotNone(result)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)

    def test_iso_format(self):
        result = parse_date("2024-01-15", ["%Y-%m-%d"])
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)

    def test_multiple_formats(self):
        result = parse_date("2024-01-15", ["%m/%d/%Y", "%Y-%m-%d"])
        self.assertIsNotNone(result)

    def test_no_match(self):
        result = parse_date("not a date", ["%m/%d/%Y"])
        self.assertIsNone(result)


class TestProfiles(unittest.TestCase):
    def test_list_profiles(self):
        profiles = list_profiles()
        self.assertIn("chase", profiles)
        self.assertIn("bofa", profiles)
        self.assertIn("generic", profiles)

    def test_get_profile(self):
        profile = get_profile("chase")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.bank_name, "Chase")

    def test_get_unknown_profile(self):
        self.assertIsNone(get_profile("nonexistent_bank"))

    def test_detect_chase(self):
        headers = ["Posting Date", "Description", "Amount", "Type", "Balance"]
        profile = detect_profile(headers)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.bank_name, "Chase")

    def test_detect_capitalone(self):
        headers = ["Transaction Date", "Transaction Description", "Debit", "Credit", "Balance"]
        profile = detect_profile(headers)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.bank_name, "Capital One")


class TestParseCSV(unittest.TestCase):
    def _write_csv(self, headers, rows):
        """Write a temporary CSV file and return its path."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        f.close()
        return f.name

    def test_chase_format(self):
        path = self._write_csv(
            ["Posting Date", "Description", "Amount", "Type", "Balance"],
            [
                ["01/15/2024", "GROCERY STORE", "-45.67", "DEBIT", "1234.56"],
                ["01/16/2024", "PAYROLL DEPOSIT", "2500.00", "CREDIT", "3734.56"],
            ],
        )
        try:
            txns = parse_csv_statement(path)
            self.assertEqual(len(txns), 2)
            self.assertEqual(txns[0].description, "GROCERY STORE")
            self.assertAlmostEqual(txns[0].amount, -45.67)
            self.assertTrue(txns[0].is_debit)
            self.assertEqual(txns[1].description, "PAYROLL DEPOSIT")
            self.assertAlmostEqual(txns[1].amount, 2500.00)
            self.assertTrue(txns[1].is_credit)
        finally:
            os.unlink(path)

    def test_debit_credit_columns(self):
        path = self._write_csv(
            ["Transaction Date", "Transaction Description", "Debit", "Credit", "Balance"],
            [
                ["2024-01-15", "Coffee Shop", "5.50", "", "994.50"],
                ["2024-01-16", "Direct Deposit", "", "3000.00", "3994.50"],
            ],
        )
        try:
            txns = parse_csv_statement(path)
            self.assertEqual(len(txns), 2)
            self.assertAlmostEqual(txns[0].amount, -5.50)
            self.assertAlmostEqual(txns[1].amount, 3000.00)
        finally:
            os.unlink(path)

    def test_explicit_profile(self):
        path = self._write_csv(
            ["Date", "Description", "Amount"],
            [
                ["01/20/2024", "Gas Station", "-35.00"],
            ],
        )
        try:
            profile = get_profile("generic")
            txns = parse_csv_statement(path, profile=profile)
            self.assertEqual(len(txns), 1)
            self.assertEqual(txns[0].bank, "Generic")
        finally:
            os.unlink(path)

    def test_empty_file(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        f.write("")
        f.close()
        try:
            txns = parse_csv_statement(f.name, profile=get_profile("generic"))
            self.assertEqual(txns, [])
        finally:
            os.unlink(f.name)

    def test_account_name_tagged(self):
        path = self._write_csv(
            ["Date", "Description", "Amount"],
            [
                ["01/20/2024", "Test", "-10.00"],
            ],
        )
        try:
            txns = parse_csv_statement(path, profile=get_profile("generic"), account_name="Checking")
            self.assertEqual(txns[0].account, "Checking")
        finally:
            os.unlink(path)


class TestCombiner(unittest.TestCase):
    def _make_txn(self, day, desc, amount, source="file1.csv"):
        return Transaction(
            date=date(2024, 1, day),
            description=desc,
            amount=amount,
            source_file=source,
        )

    def test_combine_sorts(self):
        list1 = [self._make_txn(3, "C", -10)]
        list2 = [self._make_txn(1, "A", -20)]
        combined = combine_transactions([list1, list2])
        self.assertEqual(combined[0].description, "A")
        self.assertEqual(combined[1].description, "C")

    def test_dedup_cross_file(self):
        txn1 = self._make_txn(1, "Coffee", -5.00, "jan.csv")
        txn2 = self._make_txn(1, "Coffee", -5.00, "jan_backup.csv")
        combined = combine_transactions([[txn1], [txn2]])
        self.assertEqual(len(combined), 1)

    def test_dedup_same_file_keeps_both(self):
        txn1 = self._make_txn(1, "Coffee", -5.00, "jan.csv")
        txn2 = self._make_txn(1, "Coffee", -5.00, "jan.csv")
        combined = combine_transactions([[txn1, txn2]])
        self.assertEqual(len(combined), 2)

    def test_no_dedup(self):
        txn1 = self._make_txn(1, "Coffee", -5.00, "a.csv")
        txn2 = self._make_txn(1, "Coffee", -5.00, "b.csv")
        combined = combine_transactions([[txn1], [txn2]], deduplicate=False)
        self.assertEqual(len(combined), 2)

    def test_summary(self):
        txns = [
            self._make_txn(1, "Debit", -100),
            self._make_txn(2, "Credit", 200),
        ]
        summary = compute_summary(txns)
        self.assertEqual(summary["total_transactions"], 2)
        self.assertEqual(summary["total_debits"], -100.0)
        self.assertEqual(summary["total_credits"], 200.0)
        self.assertEqual(summary["net"], 100.0)

    def test_empty_summary(self):
        summary = compute_summary([])
        self.assertEqual(summary["total_transactions"], 0)


class TestExporter(unittest.TestCase):
    def test_export_csv(self):
        txns = [
            Transaction(
                date=date(2024, 1, 15),
                description="Test Purchase",
                amount=-25.50,
                bank="Chase",
            ),
            Transaction(
                date=date(2024, 1, 16),
                description="Deposit",
                amount=1000.00,
                bank="Chase",
            ),
        ]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = f.name
        try:
            result = export_csv(txns, output_path)
            self.assertTrue(os.path.exists(result))

            with open(result, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["Description"], "Test Purchase")
            self.assertEqual(rows[0]["Amount"], "-25.5")
        finally:
            os.unlink(output_path)

    def test_export_csv_with_summary(self):
        txns = [
            Transaction(date=date(2024, 1, 1), description="A", amount=-10),
        ]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = f.name
        try:
            export_csv(txns, output_path, include_summary=True)
            with open(output_path, "r") as f:
                content = f.read()
            self.assertIn("# Summary", content)
        finally:
            os.unlink(output_path)


class TestTransaction(unittest.TestCase):
    def test_to_dict(self):
        t = Transaction(date=date(2024, 1, 1), description="Test", amount=-10)
        d = t.to_dict()
        self.assertEqual(d["Date"], "2024-01-01")
        self.assertEqual(d["Amount"], -10)
        self.assertEqual(d["Type"], "Debit")

    def test_dedup_key(self):
        t1 = Transaction(date=date(2024, 1, 1), description="Coffee", amount=-5)
        t2 = Transaction(date=date(2024, 1, 1), description="coffee", amount=-5)
        self.assertEqual(t1.dedup_key(), t2.dedup_key())

    def test_is_debit_credit(self):
        t = Transaction(date=date(2024, 1, 1), description="X", amount=-10)
        self.assertTrue(t.is_debit)
        self.assertFalse(t.is_credit)


if __name__ == "__main__":
    unittest.main()
