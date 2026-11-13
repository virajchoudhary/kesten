"""Check legacy display naming without loading experimental model modules."""

import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class DisplayBrandingTests(unittest.TestCase):
    def test_revisable_legacy_page_titles(self):
        for name, expected in [(None, "Kerquant"), ("  ", "Kerquant"), ("Review", "Review")]:
            with self.subTest(name=name), patch.dict(os.environ):
                if name is None:
                    os.environ.pop("NEXT_PUBLIC_PRODUCT_NAME", None)
                else:
                    os.environ["NEXT_PUBLIC_PRODUCT_NAME"] = name
                brand = runpy.run_path(str(ROOT / "frontend/branding.py"))
                self.assertEqual(brand["PRODUCT_NAME"], expected)
                self.assertEqual(brand["page_title"]("Research"), f"Research - {expected}")

    def test_rebranded_legacy_pages_compile_without_loading_models(self):
        files = [ROOT / "frontend/app.py", ROOT / "frontend/Home.py", *sorted((ROOT / "frontend/pages").rglob("*.py"))]
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
