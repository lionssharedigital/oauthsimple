"""Allow running as: python -m bank_statement_parser"""

from .cli import main
import sys

sys.exit(main())
