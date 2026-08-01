"""Krause register prefixes: `Tn6` and `PM13` are KM numbers; `PnA16` is a Pn.

Krause does not number everything with bare digits. Non-circulation series get a
register-code prefix, and the Bruun catalogue prints them verbatim:

    KM-Tn6      Danish Rigsbanktegn (token), 4 Skilling 1815
    KM-PM13     Swedish plate money, 8 Daler 1659
    KM-A140     ordinary letter-prefixed variant
    KM-PnA16    pattern / presentation register, with a SERIES letter

Two independent regex bugs threw these away:

  * `REF_PATTERNS["KM"]` allowed exactly ONE prefix letter, so every two-letter
    register (`Tn`, `PM`) failed to match — 15 lots carried a KM the seed never
    saw.
  * `REF_PATTERNS["Pn"]` demanded a digit straight after «Pn», so the nine
    series-letter forms (`PnA16`, `PnH16`, `PnJ16`, `PnG16`, `PnA8`, `PnB19`,
    `PnA52`, `PnA60`, `PnA63`) matched neither pattern. Four of them sit on
    lots that DO reach the seed, and the Pn marker is the §9 item-5 gate for
    the off-nominal test — losing it disarmed that test on the coins it exists
    for. Bruun-6276 (lot 1070, «3 Ducats» 1659, KM-PnA16) was where this
    surfaced, 2026-07-31.

Pn stays OUT of `km` on purpose: it is a separate Krause register, and `Pn10`
recurs across reigns exactly as bare numbers do, so folding it into `km` would
manufacture the §9.4 base-collision the merger reads as evidence of one coin.

Run:
    .venv/bin/python -m unittest tests.test_bruun_km_register_prefixes -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots", PROJECT_ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["bruun_parse_lots"] = _mod
_spec.loader.exec_module(_mod)

KM = _mod.REF_PATTERNS["KM"]
PN = _mod.REF_PATTERNS["Pn"]


def km(text: str) -> str | None:
    m = KM.search(text)
    return m.group(1) if m else None


def pn(text: str) -> str | None:
    m = PN.search(text)
    return m.group(1) if m else None


class TestKmRegisterPrefixes(unittest.TestCase):
    def test_two_letter_registers(self):
        # Real bodies: lot 17155 (Rigsbanktegn), lot 12197 (plate money).
        self.assertEqual(km("… NGC MS-63. KM-Tn6; Sieg-3; …"), "Tn6")
        self.assertEqual(km("… KM-PM13; SM-…"), "PM13")
        self.assertEqual(km("… KM-PMA48; …"), "PMA48")

    def test_single_letter_and_bare_still_work(self):
        for text, want in (
            ("Fr-213; KM-A140; Hede-36", "A140"),
            ("KM-455; Hede-57", "455"),
            ("KM# 138.2; Dav-…", "138.2"),
            ("KM-651.1", "651.1"),
        ):
            with self.subTest(text=text):
                self.assertEqual(km(text), want)

    def test_pattern_register_is_not_a_km(self):
        # §9.4 — `Pn10` recurs across reigns; admitting it to `km` would forge
        # a base collision the merger reads as "one coin".
        for text in ("Fr-127; KM-PnA16; Hede-99", "KM-Pn54; Hede-14"):
            with self.subTest(text=text):
                self.assertIsNone(km(text))

    def test_unlisted_and_cf_forms_still_rejected(self):
        # D31 keeps «cf.» and «unlisted» out of catalog fields; the widened
        # prefix must not start swallowing them.
        for text in (
            "Fr-unlisted; KM-unlisted (cf. 645 in silver); Hede-25",
            "KM-cf. 15; Lange-…",
            "Fr-unlisted (cf. 124); KM-PnJ16",   # the KM here is a Pn → None
        ):
            with self.subTest(text=text):
                self.assertIsNone(km(text))


class TestPnSeriesLetter(unittest.TestCase):
    def test_series_letter_forms(self):
        # The four that reach the seed, plus the pattern-flagged ones.
        for text, want in (
            ("Fr-127; KM-PnA16; Hede-99; Sieg-52", "PnA16"),
            ("Fr-123; KM-PnH16; Hede-99", "PnH16"),
            ("Fr-unlisted (cf. 124); KM-PnJ16; Hede-100A", "PnJ16"),
            ("KM-PnG16; Hede-…", "PnG16"),
            ("KM-PnA8; …", "PnA8"),
        ):
            with self.subTest(text=text):
                self.assertEqual(pn(text), want)

    def test_digit_forms_unchanged(self):
        for text, want in (("KM-Pn54; Hede-14", "Pn54"),
                           ("KM-Pn39; Hede-36", "Pn39"),
                           ("KM-Pn3c; …", "Pn3c")):
            with self.subTest(text=text):
                self.assertEqual(pn(text), want)

    def test_does_not_fire_on_unrelated_text(self):
        for text in ("Pattern 6 Skilling", "Penning of 1523", "KM-455; Hede-57"):
            with self.subTest(text=text):
                self.assertIsNone(pn(text))


class TestOthersUnionKeepsListForm(unittest.TestCase):
    """`catalog.others` must UNION on regen, and must stay a list.

    Two bugs, one after the other:

      * `others` was absent from the merge's list-capable set, so it was
        existing-wins — a catalogue code the parser newly learns to read could
        never reach an entry that already existed. The Pn fix above produced
        `Pn# PnA16` on four lots and not one of them landed in the seed.
      * The first attempt routed it through `_union_cat_values`, which collapses
        a singleton back to a SCALAR. That is correct for `km` / `hede` / `sieg`
        (schema `str | list`) and wrong for `others` (schema `list[str]`): it
        rewrote 800+ seed lines into `others: Ernst 1940 3-13` before the diff
        was inspected. Hence a dedicated helper.
    """

    def setUp(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from lib.seed_merge import _union_others
        self.u = _union_others

    def test_always_returns_a_list(self):
        for a, b in ((["X# 1"], ["X# 1"]), (None, ["X# 1"]), (["X# 1"], None),
                     ("X# 1", "X# 1")):
            with self.subTest(a=a, b=b):
                self.assertIsInstance(self.u(a, b), list)

    def test_fresh_value_is_added_not_dropped(self):
        self.assertEqual(
            self.u(["Aagaard# 74.1"], ["Aagaard# 74.1", "Pn# PnA16"]),
            ["Aagaard# 74.1", "Pn# PnA16"])

    def test_idempotent_across_reseeds(self):
        once = self.u(["Aagaard# 5.1"], ["Aagaard# 5.1"])
        twice = self.u(once, ["Aagaard# 5.1"])
        self.assertEqual(once, twice)
        self.assertEqual(once, ["Aagaard# 5.1"])

    def test_existing_leads_and_dedups_loosely(self):
        self.assertEqual(self.u(["A# 1"], ["a#  1", "B# 2"]), ["A# 1", "B# 2"])

    def test_none_entries_dropped(self):
        self.assertEqual(self.u([None], ["X# 1"]), ["X# 1"])


if __name__ == "__main__":
    unittest.main()
