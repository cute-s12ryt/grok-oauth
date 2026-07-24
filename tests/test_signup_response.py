import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "grok-build-auth"))

from xconsole_client.client import XConsoleAuthClient


class SignupResponseClassificationTests(unittest.TestCase):
    def test_unknown_http_200_body_fails_closed(self) -> None:
        self.assertFalse(
            XConsoleAuthClient._signup_response_looks_ok(
                "unknown-success-body",
                [],
                {},
            )
        )

    def test_known_rsc_flight_is_success(self) -> None:
        body = '2:"$Sreact.fragment"\nc:I[443085,["/_next/static/chunks/app.js"]]'
        self.assertTrue(XConsoleAuthClient._signup_response_looks_ok(body, [], {}))

    def test_structured_signup_error_is_failure(self) -> None:
        body = '{"code":"account_email_already_exists"}'
        self.assertFalse(XConsoleAuthClient._signup_response_looks_ok(body, [], {}))

    def test_sso_cookie_is_strong_success_evidence(self) -> None:
        self.assertTrue(
            XConsoleAuthClient._signup_response_looks_ok(
                "",
                ["sso=header.payload.signature; Path=/; HttpOnly"],
                {},
            )
        )


if __name__ == "__main__":
    unittest.main()
