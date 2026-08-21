"""Four parser defects, each of which silently narrowed what a source said.

All four were found by reading the cached source texts against the values the
pipeline had stored (2026-08-21), while auditing why 18 finals carried a mint
no member attested. None of them produced an error or an empty field — each
returned a confident, plausible, WRONG value, which is why they survived.

  1. `_canonicalise_mint` ate «(?)».  Hede's index prints «København (?)»;
     the gloss-strip ran before the uncertainty check, so the seed stored a
     certain «Kopenhagen» and `mint_verified: true`. 4 seeds affected —
     dk-hede-c4h28, dk-hede-c7hej, dk-hede-f6h35, dk-hede-nc5h64.

  2. `parse_ngc._STRUCK_AT` kept only the first mint of a list, and was
     case-sensitive so lowercase clauses matched nothing. 15 NGC records name
     more than one mint; 10 lost at least one. Five read «Struck at
     Copenhagen, Altona and Kongsberg» and came back as «Copenhagen» — the
     reason km-616-chr-v-1771's stored Kongsberg looked unsourced.

  3. `_canonicalise_mint` did not know the Danish conjunction. KMM writes a
     joint issue as «København og Altona» (12 records); it travelled as one
     unknown token. The split has to be conditional: «Slesvig og Holsten»
     (47) and «Holsten og Gottorp» (14) are region pairs, not mints.

  4. Galster's mint vocabulary existed in three drifting copies, none with
     the Norwegian mints. A name missing from the list does not yield
     «unknown» — it yields the first name the parser DOES know from anywhere
     on the page, so a Nidaros coin was recorded as struck at Bergen.

Run via:
    .venv/bin/python -m unittest tests.test_mint_source_fidelity -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import parse_ngc  # noqa: E402
from lib.galster_parsers.common import MINT_ALTERNATIVE, MINT_WORD  # noqa: E402
from lib.v2_seed_writer import _canonicalise_mint  # noqa: E402


class TestUncertaintyMarkerSurvives(unittest.TestCase):
    """Defect 1 — «X (?)» is the source doubting, not a gloss."""

    def test_paren_question_becomes_trailing_marker(self):
        # danskmoent f6hede.htm, Hede 35: «2 Rigsbankskilling | Kobber |
        # 1818 | København (?)»
        self.assertEqual(_canonicalise_mint("København (?)"), "Kopenhagen?")

    def test_norwegian_case_too(self):
        # danskmoent, Hede Norge 64: «Christiania (?)»
        self.assertEqual(_canonicalise_mint("Christiania (?)"), "Christiania?")

    def test_real_gloss_is_still_stripped(self):
        self.assertEqual(_canonicalise_mint("Altona (FK VS)"), "Altona")
        self.assertEqual(
            _canonicalise_mint("Glückstadt, Schleswig-Holstein"), "Glückstadt")

    def test_existing_trailing_form_unchanged(self):
        self.assertEqual(_canonicalise_mint("København?"), "Kopenhagen?")


class TestJointMintConjunction(unittest.TestCase):
    """Defect 3 — «og» joins two mints; it also joins two regions."""

    def test_kmm_joint_mint_splits(self):
        # KMM 578767 / 578768, `place`: «København og Altona»
        self.assertEqual(
            _canonicalise_mint("København og Altona"), ["Altona", "Kopenhagen"])

    def test_english_and_german_conjunctions(self):
        self.assertEqual(
            _canonicalise_mint("Copenhagen and Altona"), ["Altona", "Kopenhagen"])

    def test_region_pair_must_not_split(self):
        # 47 KMM records; neither arm is a mint, so the string stays whole
        # rather than inventing two mints named after duchies.
        self.assertEqual(
            _canonicalise_mint("Slesvig og Holsten"), "Slesvig og Holsten")
        self.assertEqual(
            _canonicalise_mint("Holsten og Gottorp"), "Holsten og Gottorp")

    def test_ambiguity_marker_is_not_a_conjunction(self):
        # «eller» = or, and stays whole here: absorb's ambiguity-split owns
        # it, and it must also drop mint_verified, which «og» must not.
        self.assertEqual(
            _canonicalise_mint("Hamar (Norge) eller København"),
            "Hamar (Norge) eller København")


class TestNgcStruckAt(unittest.TestCase):
    """Defect 2 — every mint NGC names, and only for THIS coin."""

    def struck(self, note):
        return parse_ngc.parse_note(note).get("flags", {}).get("struck_at")

    def test_three_mint_list(self):
        # cuid 1052647 / 1069292 / 1052363 / 1062479 / 1068824
        self.assertEqual(
            self.struck("Size varies. Struck at Copenhagen, Altona and Kongsberg."),
            ["Copenhagen", "Altona", "Kongsberg"])

    def test_two_mints_with_trailing_common_noun(self):
        # cuid 1153433: «Struck at Oldendorf and Altona mints»
        self.assertEqual(
            self.struck("Varieties exist. Struck at Oldendorf and Altona mints."),
            ["Oldendorf", "Altona"])

    def test_two_separate_clauses(self):
        # cuid 1050293: both are mints of this type, and the verb is lowercase
        self.assertEqual(
            self.struck("Dav. #1310. 1786 date struck at Poppelbüttel, "
                        "others struck at Altona."),
            ["Poppelbüttel", "Altona"])

    def test_lowercase_single_clause(self):
        # cuid 171190 etc. — matched nothing at all before
        self.assertEqual(self.struck("Ref. B-100. struck at Rinteln mint."),
                         "Rinteln")

    def test_similar_type_is_another_coin(self):
        # cuid 1102813 / 1102016 / 1051146 / 1051147: this note is ABOUT a
        # different KM#. Now that the lowercase verb matches, the exclusion
        # has to be explicit or we would attribute another type's mint here.
        self.assertIsNone(
            self.struck("Similar type with very minor differences also struck "
                        "at Kongsberg Mint and listed under Denmark as KM#Tn1."))

    def test_single_mint_shapes_unchanged(self):
        self.assertEqual(self.struck("Struck at Altona."), "Altona")
        self.assertEqual(self.struck("Struck at Christiania Mint."), "Christiania")
        self.assertEqual(
            self.struck("Struck in Copenhagen for the Danish West Indies Company."),
            "Copenhagen")

    def test_next_sentence_does_not_bleed_into_the_name(self):
        # cuid 1049854 stored «Altona. Mintmasters»; 1050251 «Kongsberg. Three»
        self.assertEqual(self.struck("Struck at Altona. Mintmasters vary."),
                         "Altona")

    def test_source_spelling_is_preserved(self):
        # NGC's own typo. Phase 2 records what the page says (§0); mapping it
        # to Kongsberg is the seed layer's alias table, not the parser's call.
        self.assertEqual(
            self.struck("Struck at Copenhagen, Altona and Kongberg."),
            ["Copenhagen", "Altona", "Kongberg"])


class TestGalsterMintVocabulary(unittest.TestCase):
    """Defect 4 — one vocabulary, and both arms of «eller»."""

    def test_norwegian_mints_are_known(self):
        for name in ("Hamar", "Christiania", "Nidaros", "Kongsberg"):
            self.assertRegex(name, MINT_WORD, f"{name} missing from MINT_WORD")

    def test_alternative_captures_both_arms(self):
        # norge_nc2g174: «Hamar (Norge) eller København» → was «København»
        m = re.search(MINT_ALTERNATIVE, "Hamar (Norge) eller København")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(0), "Hamar (Norge) eller København")
        # norge_nc2g172: «Hamar eller Oslo» → was «Oslo»
        m = re.search(MINT_ALTERNATIVE, "1532 (Unik), Hamar eller Oslo (Norge).")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(0), "Hamar eller Oslo")

    def test_single_vocabulary_not_three_copies(self):
        from lib.galster_parsers import grevenfejde, standard
        self.assertIs(grevenfejde._MINT_WORD, MINT_WORD)
        self.assertIn("Nidaros", standard.MINT_WORD)


if __name__ == "__main__":
    unittest.main()
