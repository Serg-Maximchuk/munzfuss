# tests/

## Running them

```bash
.venv/bin/python -m unittest discover tests -v      # everything
.venv/bin/python -m unittest tests.test_v2_index_layers -v   # one file
```

**`unittest`, from the standard library — pytest is NOT installed**, and
`.venv/bin/python -m pytest` fails with `No module named pytest`. 90 of the 92
files here are unittest and nothing said so anywhere, so the mistake of writing
a pytest file and discovering it only at the run is easy and has been made.

A live-corpus test loads the whole V2 index and takes ~2 minutes. Run it in the
background, per CLAUDE.md «Run (re)builds … in the background».

## Writing one

Two conventions, both near-universal here and neither previously written down.

**1. Open with the story, not the mechanics.** 91 of 92 files begin with a
module docstring that says what broke, how it was found, and why it survived —
not what the test asserts, which the test already says. Someone reading a
failure a year from now needs the reason the guard exists.

**2. The path preamble.** Tests live outside `scripts/`, so imports need it:

```python
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))                    # lib.*
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))    # builders, mergers
```

Skeleton:

```python
"""What broke, how it was found, and why it did not announce itself."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.something import thing  # noqa: E402


class WhatItGuards(unittest.TestCase):
    def test_the_specific_regression(self):
        """One sentence on the case, if the name cannot carry it."""
        self.assertEqual(thing("in"), "out")


if __name__ == "__main__":
    unittest.main()
```

## What is worth a test here

The failures this project actually suffers are **silent wrong answers**, not
crashes — a parser that narrows what a source said, a lookup keyed on the wrong
id layer, a filter that drops a coin nobody notices. So the tests that earn
their place pin a *specific* defect with its real data:
`test_absence_does_not_veto`, `test_bruun_bare_pn_is_not_a_skip`,
`test_v2_index_layers`. A test that restates a function's signature does not.

Synthetic fixtures for the mechanism, one live-corpus assertion for the shape —
and assert the SHAPE of the live number, never the number, which moves with the
data (`assertGreater(reached, total // 2)`, not `assertEqual(reached, 14022)`).
