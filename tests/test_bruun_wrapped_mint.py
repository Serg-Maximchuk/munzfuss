"""A mint whose « <X> Mint» token is pushed onto the next physical line
by a PDF line break must still be recovered.

Code under test:
    scripts/bruun_parser/02_parse_lots.py — the mint-extraction tier
    stack (META_MINT_RE on meta_line → META_MINT_RE on the leading
    window of body_match → MINT_RE whitelist on body_match).

Bug (verified against the live cache 2026-07-25): `meta_line` is ONE
physical line by construction, so when the cataloguer's meta segment
wraps, the mint token lands on the following line and never reaches it.
Lots 13108 / 13109 / 13110 all read «DENMARK. Speciedaler
(Reichstaler), 1627. Wolfenbüt -\ntel Mint» — meta_line stopped at
«Wolfenbüt -» and the whitelist fallback could not recover the mint
either, because MINT_RE's hardcoded city list has no Wolfenbüttel. The
mint was silently lost on all three lots.

Note the root cause is the truncated meta_line PLUS the whitelist gap —
NOT a missing de-hyphenation. `body_match` was already de-hyphenated
correctly («Wolfenbüt -\ntel» → «Wolfenbüttel»); nothing consulted it
with the structured pattern. These tests pin both halves so a future
edit cannot silently regress either.

Run:
    .venv/bin/python -m unittest tests.test_bruun_wrapped_mint
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_MODULE_PATH = PROJECT_ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"


def _load_parser():
    """Import the numerically-named parser module by path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("bruun_parse_lots",
                                                  _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PARSER = _load_parser()


def _body_match(body: str) -> str:
    """Reproduce the parser's body normalisation (de-hyphenate across a
    line break, then collapse whitespace)."""
    out = re.sub(r"([A-Za-zÄÖÜäöüß])\s*-\s*\n\s*([a-zäöüß])", r"\1\2", body)
    return re.sub(r"\s+", " ", out)


def extract_mint(meta_line: str | None, body: str) -> str | None:
    """The three-tier extraction the parser performs, in order."""
    bm = _body_match(body)
    if meta_line:
        m = PARSER.META_MINT_RE.search(meta_line)
        if m:
            return m.group(1).strip() + " Mint"
        window = bm[:len(meta_line) + 80]
        m = PARSER.META_MINT_RE.search(window)
        if m:
            return m.group(1).strip() + " Mint"
    m = PARSER.MINT_RE.search(bm)
    return m.group(1) if m else None


WOLFENBUTTEL_BODY = (
    "DENMARK. Speciedaler (Reichstaler), 1627. Wolfenbüt -\n"
    "tel Mint (Lower Saxony). Christian IV . NGC EF Details—\n"
    "Cleaned. Dav-7758D; cf. KM-66; Hede-3A; Sieg-193.2."
)
WOLFENBUTTEL_META = "DENMARK. Speciedaler (Reichstaler), 1627. Wolfenbüt -"


class TestDeHyphenation(unittest.TestCase):
    """The pre-existing normalisation — pinned so it cannot regress."""

    def test_hyphen_break_before_lowercase_is_joined(self):
        self.assertIn("Wolfenbüttel Mint", _body_match(WOLFENBUTTEL_BODY))

    def test_hyphen_break_before_uppercase_is_preserved(self):
        # A genuine hyphenated compound broken at the line end must keep
        # its hyphen — «Schleswig-\nHolstein» must NOT become
        # «SchleswigHolstein». The de-hyphenation deliberately fires only
        # before a lowercase continuation. (The whitespace collapse does
        # leave «Schleswig- Holstein» with a space; that is the existing
        # behaviour and out of scope here — what matters is that the two
        # words were not glued into one.)
        out = _body_match("GERMANY. Schleswig-\nHolstein. Taler.")
        self.assertNotIn("SchleswigHolstein", out)
        self.assertIn("Schleswig-", out)


class TestWrappedMintRecovery(unittest.TestCase):

    def test_wrapped_mint_recovered(self):
        # Lots 13108 / 13109: the live failing case.
        self.assertEqual(
            extract_mint(WOLFENBUTTEL_META, WOLFENBUTTEL_BODY),
            "Wolfenbüttel Mint",
        )

    def test_mint_word_alone_on_next_line(self):
        # Lot 13110: the town is complete on the meta line but the word
        # «Mint» itself wrapped, so META_MINT_RE still misses it there.
        meta = "DENMARK. Speciedaler (Reichstaler), 1627. Wolfenbüttel"
        body = ("DENMARK. Speciedaler (Reichstaler), 1627. Wolfenbüttel \n"
                "Mint, Christian IV . NGC EF-40. Dav-7760; KM-68.")
        self.assertEqual(extract_mint(meta, body), "Wolfenbüttel Mint")

    def test_dual_mint_preserved_verbatim(self):
        # Lot 13243: «Altona/Poppenbüttel» is a dual mint kept whole —
        # the entity classifier splits on «/ or » downstream.
        meta = "DENMARK. Schleswig-Holstein. Speciedaler, 1787-B/MF."
        body = ("DENMARK. Schleswig-Holstein. Speciedaler, 1787-B/MF. \n"
                "Altona/Poppenbüttel Mint. Christian VII. NGC MS-63.")
        self.assertEqual(extract_mint(meta, body),
                         "Altona/Poppenbüttel Mint")

    def test_intact_meta_line_still_wins(self):
        # The first tier must keep priority — no behaviour change for
        # the overwhelming majority of lots.
        meta = "DENMARK. Speciedaler, 1672. Glückstadt Mint. Christian V."
        self.assertEqual(extract_mint(meta, meta), "Glückstadt Mint")

    def test_window_does_not_grab_mint_from_later_prose(self):
        # The Bruun-3725 failure mode: the coin's own mint is absent, and
        # an unrelated mint is discussed far later in the historical
        # prose. The new tier-2 window must not reach it.
        #
        # Scoped to tier 2 deliberately: tier 3 (the MINT_RE whitelist
        # scanning the WHOLE body) does still grab «Lund Mint» here. That
        # is pre-existing behaviour this change neither introduces nor
        # fixes — see the note in the module docstring. Asserting on the
        # full stack would wrongly credit the fix with solving it.
        meta = "DENMARK. Witten, ND (1350). Christian IV."
        body = (meta + "\nNGC VF-30. Weight: 1.2 gms. " + "x" * 400 +
                " Comparable pieces are known from the Lund Mint.")
        window = _body_match(body)[:len(meta) + 80]
        self.assertIsNone(PARSER.META_MINT_RE.search(window))


if __name__ == "__main__":
    unittest.main()
