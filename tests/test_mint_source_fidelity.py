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


class TestSourceSpellingAliases(unittest.TestCase):
    """Spelling variants the sources actually print, mapped to the mint the
    source means. Each was verified against that record's own context — ruler,
    denomination, year and the mint's operating dates — not by letter
    similarity. See the per-entry comments in `lib/mint_registry.py`.
    """

    def test_ngc_misspellings(self):
        self.assertEqual(_canonicalise_mint("Altoona"), "Altona")
        self.assertEqual(_canonicalise_mint("Kongberg"), "Kongsberg")
        self.assertEqual(_canonicalise_mint("Retwisch"), "Rethwisch")
        self.assertEqual(_canonicalise_mint("Petwisch"), "Rethwisch")
        self.assertEqual(_canonicalise_mint("Poppelbüttel"), "Poppenbüttel")

    def test_hede_own_spelling(self):
        # danskmoent c7h6/c7h7: «1 Speciedaler, Rethwitsch». Previously fixed
        # only by a private map inside build_hede_denmark_seed.py.
        self.assertEqual(_canonicalise_mint("Rethwitsch"), "Rethwisch")

    def test_kmm_spellings(self):
        # 126 records; KMM writes «Kongsberg» correctly on 443 others.
        self.assertEqual(_canonicalise_mint("Kongsborg"), "Kongsberg")
        # ES surface truncates; KMM's own web rådata writes «Glückstadt».
        self.assertEqual(_canonicalise_mint("Glückstad"), "Glückstadt")
        # A bare «Hamburg» used to be stripped as a region word and returned
        # None. That was the prefix-vs-registry collision, fixed since: the
        # motivating string the old comment cited («Hamburg, Altona») occurs
        # nowhere in the harvest cache, while 160 seed entries lost a mint the
        # source had named. See TestRegionWordVersusMint below.
        self.assertEqual(_canonicalise_mint("Hamburg"), "Hamburg")
        # «Hamborg» is still NOT aliased — that is a separate curator call.
        self.assertEqual(_canonicalise_mint("Hamborg"), "Hamborg")

    def test_correct_spellings_still_resolve(self):
        for name, want in (("Altona", "Altona"), ("Kongsberg", "Kongsberg"),
                           ("Konsberg", "Kongsberg"), ("Rethwisch", "Rethwisch"),
                           ("Poppenbüttel", "Poppenbüttel"),
                           ("Glückstadt", "Glückstadt")):
            self.assertEqual(_canonicalise_mint(name), want)


class TestDenominationIsNotAMint(unittest.TestCase):
    """A mint town never begins with a digit.

    NGC titles a coin by both its denominations — "1/32 Thaler, Schilling" —
    and the complex-mint fallback read the pre-comma half as the mint. The
    seed-writer hygiene pass then split it on the "/" meant for
    "Hamburg/Altona", so the coin was recorded as struck at two towns called
    "1" and "32 Thaler", AND its real nominal — the fraction — was dropped.
    15 seed entries carried this.
    """

    def extract(self, nominal):
        from lib.v2_seed_writer import _extract_mint_from_nominal
        return _extract_mint_from_nominal(nominal, None)

    def test_fraction_is_not_a_mint(self):
        for nominal in ("1/32 Thaler, Schilling", "1/24 Thaler, Groschen",
                        "1/2 Portugaloser, 5 Ducat", "6 Pfennig, Sechsling"):
            _, mint = self.extract(nominal)
            self.assertIsNone(mint, f"{nominal!r} yielded mint {mint!r}")

    def test_the_nominal_survives_intact(self):
        # The fraction is the coin's own denomination and must not be
        # traded away for the second half of the title.
        nominal, _ = self.extract("1/32 Thaler, Schilling")
        self.assertIn("1/32 Thaler", nominal)

    def test_vulgar_fraction_too(self):
        _, mint = self.extract("½ Speciedaler, Schilling")
        self.assertIsNone(mint)

    def test_real_mint_extraction_unaffected(self):
        nominal, mint = self.extract("Altona, 1 Speciedaler")
        self.assertEqual(mint, "Altona")
        self.assertEqual(nominal, "1 Speciedaler")
        # Galster's ambiguous pair still comes through whole.
        _, mint = self.extract("Hamar (Norge) eller København, Søsling(?)")
        self.assertEqual(mint, "Hamar (Norge) eller København")


class TestRegionWordVersusMint(unittest.TestCase):
    """A region word is dropped; a city that happens to name a region is not.

    `_MINT_COUNTRY_PREFIXES` strips the country/region half of a source's mint
    string. Three of its nine entries — Hamburg, Lübeck, Schleswig — are also
    canonical mints in `lib/mint_registry.py`, so the by-name drop deleted the
    mint whenever a source said the coin was struck in one of those cities.
    160 seed entries across kmk, ikmk, ucoin and numista carried no mint for
    that reason alone. The drop now defers to the registry.

    Measured when this landed (2026-08-21): 160 seeds gain a mint, 3 change
    (a joint «Hamburg; Berlin» that had lost its Hamburg half), 0 change
    `issuing_entity` — none of the affected entries is `danish_realm`, so
    build.py's `_derive_issuing_entity` never fires, and none of the three
    names is in `HOLSTEIN_CROWN_MINTS`.
    """

    def test_the_three_cities_survive(self):
        self.assertEqual(_canonicalise_mint("Hamburg"), "Hamburg")
        self.assertEqual(_canonicalise_mint("Lübeck"), "Lübeck")
        self.assertEqual(_canonicalise_mint("Schleswig"), "Schleswig")

    def test_real_region_words_still_dropped(self):
        # Leading and trailing alike — in these sources the country more often
        # TRAILS the town, which is why a positional rule would be wrong.
        self.assertEqual(_canonicalise_mint("Denmark, Copenhagen"), "Kopenhagen")
        self.assertEqual(
            _canonicalise_mint("Copenhagen, Denmark (?-1739)"), "Kopenhagen")
        self.assertEqual(_canonicalise_mint("Norway, Kongsberg"), "Kongsberg")
        self.assertEqual(_canonicalise_mint("Husum, Germany"), "Husum")
        self.assertEqual(
            _canonicalise_mint("Altona, Schleswig-Holstein, Germany"), "Altona")
        self.assertEqual(
            _canonicalise_mint("Royal Danish Mint (Den Kongelige Mønt), "
                               "Copenhagen, Denmark (1739-date)"), "Kopenhagen")

    def test_city_beside_a_region_word(self):
        # Numista writes the town FIRST here; «Germany» goes, «Schleswig» stays.
        self.assertEqual(_canonicalise_mint("Schleswig, Germany"), "Schleswig")

    def test_joint_mint_keeps_both_halves(self):
        # ucoin: Hamburg was being deleted out of a genuine joint mint.
        self.assertEqual(
            _canonicalise_mint("Hamburg, Berlin (A)"), ["Berlin", "Hamburg"])
        self.assertEqual(
            _canonicalise_mint("Hamburg; Berlin"), ["Berlin", "Hamburg"])

    def test_institution_gloss_still_stripped(self):
        self.assertEqual(
            _canonicalise_mint("Hamburg Mint (Hamburgische Münze)"), "Hamburg")

    def test_paren_tail_forms_unchanged(self):
        # The city in parentheses is a disambiguating gloss on ANOTHER town,
        # not a second mint — these must not start resolving to Hamburg.
        self.assertEqual(_canonicalise_mint("Harburg (Hamburg)"), "Harburg")
        self.assertEqual(_canonicalise_mint("Altona (Hamburg)"), "Altona")
        self.assertEqual(_canonicalise_mint("J (Hamburg)"), "J")
        self.assertEqual(
            _canonicalise_mint("Glückstadt, Schleswig-Holstein"), "Glückstadt")

    def test_compound_region_names_untouched(self):
        self.assertEqual(_canonicalise_mint("Holstein-Gottorp"), "Holstein-Gottorp")
        self.assertEqual(_canonicalise_mint("Slesvig-Holsten"), "Slesvig-Holsten")

    def test_prefix_list_and_registry_may_not_disagree(self):
        """The invariant, not just the symptom.

        This is the test that would have caught the original bug: any name
        present in BOTH the drop-set and the registry's alias table is a mint
        the pipeline would silently delete.
        """
        from lib.v2_seed_writer import (
            _MINT_ALIAS_TO_CANON, _MINT_COUNTRY_PREFIXES,
        )
        overlap = set(_MINT_COUNTRY_PREFIXES) & set(_MINT_ALIAS_TO_CANON)
        for name in sorted(overlap):
            self.assertIsNotNone(
                _canonicalise_mint(name.title()),
                f"{name!r} is in the drop-set AND the registry, and resolves "
                f"to nothing — the collision is back")


class TestSentencePunctuationIsNotPartOfTheName(unittest.TestCase):
    """«Altona.» must collapse onto «Altona».

    A source that ends its mint statement with a full stop produced a token the
    alias table could not match, so the punctuated form never canonicalised. On
    its own that was cosmetic. It stopped being cosmetic once the parser fixes
    landed: a final that had STORED the punctuated form kept it, the corrected
    member supplied the clean one, and `_collect_mints` unioned the two into
    «Altona, Altona.» — one mint rendered as two. 19 finals showed such a pair,
    and 8 of them were being widened onto the Schleswig-Holstein page purely
    because the duplicate looked like a second, Holstein, mint.
    """

    def test_trailing_stop_collapses(self):
        self.assertEqual(_canonicalise_mint(["Altona", "Altona."]), "Altona")
        self.assertEqual(
            _canonicalise_mint(["Copenhagen.", "Kopenhagen"]), "Kopenhagen")

    def test_punctuation_before_the_mint_suffix(self):
        # The strip has to run BEFORE `strip_mint_suffix`, or «Mint.» hides it.
        self.assertEqual(
            _canonicalise_mint(["Kongsberg", "Kongsberg Mint."]), "Kongsberg")
        self.assertEqual(
            _canonicalise_mint(["Christiania", "Christiania Mint."]), "Christiania")

    def test_punctuation_before_the_alias_lookup(self):
        # «Altoona.» must reach the alias table as «Altoona».
        self.assertEqual(_canonicalise_mint(["Altona", "Altoona."]), "Altona")

    def test_uncertainty_marker_is_not_punctuation(self):
        # «?» is meaning, not typography — it must survive the strip.
        self.assertEqual(_canonicalise_mint("Ribe?"), "Ribe?")
        self.assertEqual(_canonicalise_mint("København (?)"), "Kopenhagen?")

    def test_genuine_multi_mint_still_multi(self):
        self.assertEqual(
            _canonicalise_mint(["Kopenhagen", "Rethwisch", "Rethwitsch"]),
            ["Kopenhagen", "Rethwisch"])


class TestEditionYearIsNotACatalogueIndex(unittest.TestCase):
    """«Hede 1978 nr. 119B» is number 119B in the 1978 printing.

    KMM writes some `typeNumber` values with the catalogue's EDITION YEAR in
    front. The bare-number grab took the year, so 15 seeds carried
    `hede: '1978'` — a number matching nothing, on the field the cross-source
    merger keys on. kmk-174308 («Hede 1978 nr. 119B», mint Helsingør) therefore
    never merged into the Hede-119 coin standing next to it, and its Helsingør
    read as an attestation with no member behind it — one of the five cases
    that looked like they needed a `_curation_holds` prop and did not.

    When no index follows the year, emit nothing: an absent index is honest, a
    year masquerading as one is not (§0).
    """

    def catalog(self, type_number):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))
        from build_kmk_seed import _catalog
        return _catalog({"typeNumber": type_number})

    def test_index_after_the_year_is_recovered(self):
        self.assertEqual(self.catalog("Hede 1978 nr. 119B"), {"hede": "119B"})
        self.assertEqual(self.catalog("Hede 1978 nr. 71C"), {"hede": "71C"})
        self.assertEqual(self.catalog("Hede 1978 nr. 150"), {"hede": "150"})

    def test_year_with_no_index_yields_nothing(self):
        # «Lange 1908» names the edition and no number at all.
        self.assertEqual(self.catalog("Lange 1908"), {})

    def test_plain_index_unaffected(self):
        self.assertEqual(self.catalog("Hede 134B"), {"hede": "134B"})
        self.assertEqual(self.catalog("Hbg. 4, MB 558"),
                         {"hauberg": "4", "mb": "558"})

    def test_full_remainder_catalogues_unaffected(self):
        # Aagaard deliberately stores the whole remainder, year included.
        self.assertEqual(self.catalog("Aagaard 1996 T 80"),
                         {"aagaard": "1996 T 80"})

    def test_absent_index_still_yields_nothing(self):
        self.assertEqual(self.catalog("Sch: -"), {})

    def test_index_behind_a_comma_survives_the_segment_split(self):
        """«Lange 1908, no. 306-312» — the index is printed, just after a comma.

        `_catalog` splits its input on `[;,]` first, so the comma tore «no.
        306-312» off into a fragment whose prefix («no») names no catalogue,
        and it was dropped — leaving the edition year as the only candidate.
        Caught by verify_reflow on this very session's own fix: the gate
        reported `lange` losing «1908», and recording that as a deliberate
        removal would have laundered a second bug behind the first.
        """
        self.assertEqual(self.catalog("Lange 1908, no. 306-312"),
                         {"lange": "306-312"})

    def test_year_index_join_does_not_disturb_other_commas(self):
        self.assertEqual(self.catalog("Hbg. 4, MB 558"),
                         {"hauberg": "4", "mb": "558"})
        self.assertEqual(self.catalog("G. 57, NNVM 1943 nr. 12"),
                         {"galster": "57"})
