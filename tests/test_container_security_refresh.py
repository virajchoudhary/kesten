import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED_ZLIB = "zlib=1.4-r0"


class ContainerSecurityRefreshTests(unittest.TestCase):
    def test_api_and_web_images_install_the_fixed_zlib_in_shared_layers(self):
        backend = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "RUN apk --no-logfile add --no-cache postgresql17-client=17.11-r0 zlib=1.4-r0",
            backend,
        )
        self.assertIn("krb5-libs=1.22.3-r0", backend)

        web = (ROOT / "web" / "Dockerfile").read_text(encoding="utf-8")
        base_stage, remaining_stages = web.split("FROM base AS dependencies", 1)
        self.assertIn(f"RUN apk --no-logfile add --no-cache {FIXED_ZLIB}", base_stage)
        self.assertNotIn("zlib=", remaining_stages)

    def test_api_build_tools_are_removed_in_the_same_layer(self):
        dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
        instructions = dockerfile.replace("\\\n", " ").splitlines()
        install = [line for line in instructions if line.startswith("RUN ") and "--virtual .build-deps" in line]
        self.assertEqual(len(install), 1)
        self.assertIn("python -m pip install", install[0])
        self.assertIn("apk --no-logfile del .build-deps", install[0])

    def test_refresh_image_requires_a_supplied_base_and_preserves_its_user(self):
        dockerfile = (ROOT / "deploy" / "Dockerfile.alpine-security").read_text(
            encoding="utf-8"
        )
        self.assertRegex(dockerfile, r"(?m)^ARG BASE_IMAGE$")
        self.assertRegex(dockerfile, r"(?m)^FROM \$\{BASE_IMAGE\}$")
        self.assertRegex(
            dockerfile,
            rf"(?m)^RUN apk --no-logfile add --no-cache {re.escape(FIXED_ZLIB)} \\",
        )
        self.assertIn("if apk info -e libxslt; then apk --no-logfile add --no-cache libxslt=1.1.43-r4; fi", dockerfile)
        self.assertNotRegex(dockerfile, r"(?m)^USER(?:\s|$)")

    def test_debian_refresh_pins_vendor_backport_without_changing_postgres(self):
        dockerfile = (ROOT / "deploy/Dockerfile.debian-security").read_text(encoding="utf-8")
        self.assertIn("zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1", dockerfile)
        self.assertIn("FROM ${BASE_IMAGE}", dockerfile)
        self.assertNotRegex(dockerfile, r"(?m)^USER(?:\s|$)")
        self.assertNotIn("postgresql-", dockerfile)


if __name__ == "__main__":
    unittest.main()
