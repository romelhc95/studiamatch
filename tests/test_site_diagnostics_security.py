import unittest

from scripts.shared.site_diagnostics import detect_cms


class DetectCmsSecurityTests(unittest.TestCase):
    def test_detects_hubspot_script_by_parsed_hostname(self):
        trusted_script_urls = [
            "https://hs-scripts.com/123.js",
            "https://app.hs-scripts.com/embed.js",
            "//HS-SCRIPTS.COM/forms.js",
        ]
        for src in trusted_script_urls:
            with self.subTest(src=src):
                result = detect_cms(f'<html><script src="{src}"></script></html>')

                self.assertEqual(result["cms"], "hubspot")
                self.assertIn("hubspot_scripts", result["signals"])

    def test_does_not_detect_hubspot_from_untrusted_url_substrings(self):
        untrusted_script_urls = [
            "https://attacker.example/path/hs-scripts.com/123.js",
            "https://hs-scripts.com.attacker.example/123.js",
            "https://attacker-hs-scripts.com/123.js",
            "https://attacker.example/?next=https%3A%2F%2Fhs-scripts.com",
            "https://hs-scripts.com@attacker.example/123.js",
        ]
        for src in untrusted_script_urls:
            with self.subTest(src=src):
                result = detect_cms(f'<html><script src="{src}"></script></html>')

                self.assertNotEqual(result["cms"], "hubspot")
                self.assertNotIn("hubspot_scripts", result["signals"])

    def test_detects_hubspot_mentioned_in_visible_page_text(self):
        result = detect_cms("<html><body>Powered by HubSpot</body></html>")

        self.assertEqual(result["cms"], "hubspot")
        self.assertIn("hubspot_scripts", result["signals"])

    def test_ignores_malformed_script_urls_without_aborting_diagnosis(self):
        for src in ("https://[broken", "//[broken"):
            with self.subTest(src=src):
                result = detect_cms(f'<html><script src="{src}"></script></html>')

                self.assertEqual(result["cms"], "html_puro")
                self.assertNotIn("hubspot_scripts", result["signals"])


if __name__ == "__main__":
    unittest.main()
