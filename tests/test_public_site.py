import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class PublicSiteSmokeTests(unittest.TestCase):
    def read(self, name: str) -> str:
        return (SITE / name).read_text(encoding="utf-8")

    def test_portal_is_csp_compatible_and_wired(self) -> None:
        page = self.read("portal.html")
        self.assertIn('Content-Security-Policy"', page)
        self.assertIn('<link rel="stylesheet" href="./portal.css">', page)
        self.assertIn('<script src="./portal-draft.js" defer></script>', page)
        self.assertIn('<script src="./portal.js" defer></script>', page)
        self.assertIn('id="official-channels"', page)
        self.assertNotIn("<style>", page)
        self.assertNotIn("<style ", page)

    def test_portal_has_no_production_auth_or_payment_claim(self) -> None:
        page = self.read("portal.html")
        self.assertIn("browser-only pilot workspace prototype", page)
        self.assertIn("does not create an official production identity", page)
        self.assertNotIn("Pay registration fee", page)

    def test_core_public_pages_link_to_portal(self) -> None:
        for name in ("index.html", "pilot.html", "commercial.html", "register.html"):
            page = self.read(name)
            self.assertIn('href="./portal.html"', page, name)

    def test_sitemap_includes_portal(self) -> None:
        sitemap = self.read("sitemap.xml")
        self.assertIn(
            "https://asnad68.github.io/VERQIVIA/portal.html",
            sitemap,
        )

    def test_portal_js_contains_no_external_network_call(self) -> None:
        script = self.read("portal.js")
        self.assertNotIn("fetch(", script)
        self.assertNotIn("XMLHttpRequest", script)

    def test_all_public_html_pages_have_complete_document_shell(self) -> None:
        html_files = sorted(SITE.glob("*.html"))
        self.assertTrue(html_files)
        for path in html_files:
            page = path.read_text(encoding="utf-8")
            lower = page.lower()
            with self.subTest(page=path.name):
                for tag in ("html", "head", "body"):
                    self.assertEqual(
                        len(re.findall(r"<" + tag + r"(?:\\s|>)", lower)),
                        1,
                        f"{path.name} must contain exactly one opening {tag} tag",
                    )
                    self.assertEqual(
                        len(re.findall(r"</" + tag + r"\\s*>", lower)),
                        1,
                        f"{path.name} must contain exactly one closing {tag} tag",
                    )

    def test_all_public_html_pages_have_csp_and_resolve_local_assets(self):
        html_files = sorted(SITE.glob("*.html"))
        self.assertTrue(html_files)

        for path in html_files:
            page = path.read_text(encoding="utf-8")
            with self.subTest(page=path.name):
                self.assertIn("Content-Security-Policy", page)
                script_tags = re.findall(r"<script[^>]*>", page, re.IGNORECASE)
                self.assertTrue(
                    all("src=" in tag.lower() for tag in script_tags),
                    f"{path.name} contains an inline script tag",
                )
                self.assertNotIn("<style", page.lower())
                for match in re.finditer(
                    r'''(?:href|src)="([^"]+)"''',
                    page,
                    re.IGNORECASE,
                ):
                    target = match.group(1).split("#", 1)[0].split("?", 1)[0]
                    if target in {"", ".", "./"} or target.startswith(
                        ("#", "/", "http:", "https:", "mailto:")
                    ):
                        continue
                    self.assertTrue(
                        (path.parent / target).resolve().is_file(),
                        f"{path.name} references missing local asset: {target}",
                    )



if __name__ == "__main__":
    unittest.main()
