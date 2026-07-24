r"""Regression test for the Bruun denomination extractor's TERRITORY-prefix
strip (`build_bruun_denmark_seed._denom_from_text` / `parse_denomination`).

Bug (surfaced 2026-07-24, Christian IV Wolfenbüttel occupation audit):
Bruun catalogues the Danish-king Wolfenbüttel occupation coinage of 1627
with a doubled prefix «DENMARK. Lower Saxony. <denom>, <year>.». The
`_TERRITORY_LEAD` alternation had no «Lower Saxony» token, so the strip loop
kept «Lower Saxony» as the denomination and discarded the real one
(«Speciedaler» / «Gutergroschen») as a trailing qualifier. Two live lots hit
it: Bruun-5535 (Speciedaler, Hede 3B) and Bruun-5538 (Gutergroschen, Hede 6B).

Fix: add `lower\s+saxony|niedersachsen|braunschweig|wolfenb[üu]ttel` to
`_TERRITORY_LEAD` so the region segment is stripped like every other
territory prefix, leaving the true denomination.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "maintenance"))

import build_bruun_denmark_seed as b  # noqa: E402


def test_lower_saxony_prefix_stripped():
    cases = [
        ("DENMARK. Lower Saxony. Speciedaler, 1627. Wolfenbuttel Mint. Christian IV .", "Speciedaler"),
        ("DENMARK. Lower Saxony. Gutergroschen, 1627. Wolfenbüttel Mint. Christian IV .", "Gutergroschen"),
    ]
    for meta, expected in cases:
        assert b.parse_denomination(meta, None) == expected, meta


def test_plain_denmark_prefix_still_works():
    # Single-prefix form must remain unaffected by the added tokens.
    assert b.parse_denomination(
        "DENMARK. Ducat, 1627. Wolfenbüttel Mint. Christian IV .", None) == "Ducat"
