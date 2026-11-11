"""Rules shared by more than one deliverable.

ask/ask.py (SaaS spend answer) and value/value.py (value number) must agree on
two things, so both import them from here and neither keeps its own copy:

  1. which P&L rows are SaaS rows
  2. which rows are suspected repeats, and how many

Found by the external audit of 2026-11-10: with two private copies of these
rules the tools agreed on the bundle and disagreed on changed input.

Standard library only. Python 3.8 or later.
"""
import json
import re
from pathlib import Path

import importer  # same folder: the shared parser

RULES = json.loads((Path(__file__).resolve().parent / "shared.json").read_text(encoding="utf-8"))


def _word_re(terms):
    return re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(t) for t in terms) + r")(?![A-Za-z0-9])", re.I)


def is_saas_category(label):
    """True when the category label contains a SaaS term as a whole word.

    'Software & SaaS' is SaaS. 'Software implementation services' is not: the
    word software alone does not make a row a subscription."""
    return bool(_word_re(RULES["saas_category_terms"]).search(label or ""))


def is_subtotal(label):
    return bool(_word_re(RULES["subtotal_terms"]).search(label or ""))


def similar_labels(a, b):
    """Why two labels count as near-identical, or None."""
    if a.lower().split() == b.lower().split():
        return "the labels are identical"
    if importer.word_prefix(a, b) or importer.word_prefix(b, a):
        return "one label is the other with extra words added"
    if importer.abbrev(a, b):
        return "the labels differ only by an abbreviation"
    return None


def find_repeats(items, label, amount):
    """Suspected repeats among rows of one category.

    items: rows in file order. label(row) -> str. amount(row) -> number or None.

    A row is ONE suspected repeat when an earlier row has a near-identical label
    and an equal amount. Each row is counted at most once, so three lookalike
    rows are two repeats, not three pairs. A similar label with a different
    amount is a near miss: listed, never counted.

    Returns (repeats, near_misses). repeats is a list of (earlier, later, why);
    the amount at risk is the sum of amount(later)."""
    repeats, near = [], []
    for j, later in enumerate(items):
        for earlier in items[:j]:
            why = similar_labels(label(earlier), label(later))
            if not why or amount(earlier) is None or amount(later) is None:
                continue
            if amount(earlier) == amount(later):
                repeats.append((earlier, later, why))
                break
            near.append((earlier, later))
    return repeats, near
