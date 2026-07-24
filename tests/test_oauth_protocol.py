import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "grok-build-auth"))

from xconsole_client.oauth_protocol import (
    ProtocolOAuthClient,
    SUBMIT_OAUTH2_CONSENT_ACTION,
    extract_consent_action_id,
)
from xconsole_client import xai_oauth


SPECIFIC_ACTION = "1" * 40
UNRELATED_ACTION = "2" * 40
CHUNK_ACTION = "3" * 40


class PkceStateTests(unittest.TestCase):
    def test_matching_state_returns_code(self) -> None:
        url = "http://127.0.0.1/callback?code=auth-code&state=expected"
        self.assertEqual(ProtocolOAuthClient._code_from_url(url, "expected"), "auth-code")

    def test_mismatched_state_is_rejected(self) -> None:
        url = "http://127.0.0.1/callback?code=auth-code&state=wrong"
        with self.assertRaisesRegex(RuntimeError, "state mismatch"):
            ProtocolOAuthClient._code_from_url(url, "expected")

    def test_missing_state_is_rejected(self) -> None:
        url = "http://127.0.0.1/callback?code=auth-code"
        with self.assertRaisesRegex(RuntimeError, "state mismatch"):
            ProtocolOAuthClient._code_from_url(url, "expected")


class ConsentActionExtractionTests(unittest.TestCase):
    def test_extracts_specific_inline_action(self) -> None:
        html = (
            f'createServerReference)("{SPECIFIC_ACTION}", null); '
            "submitOAuth2Consent"
        )
        self.assertEqual(extract_consent_action_id(html), SPECIFIC_ACTION)

    def test_extracts_specific_action_from_chunk(self) -> None:
        chunk = f'createServerReference)("{CHUNK_ACTION}", null); submitOAuth2Consent'
        self.assertEqual(extract_consent_action_id("<html></html>", [chunk]), CHUNK_ACTION)

    def test_specific_action_beats_earlier_unrelated_action(self) -> None:
        html = f'createServerReference)("{UNRELATED_ACTION}", null)'
        chunk = f'createServerReference)("{CHUNK_ACTION}", null); submitOAuth2Consent'
        self.assertEqual(extract_consent_action_id(html, [chunk]), CHUNK_ACTION)

    def test_falls_back_to_observed_action(self) -> None:
        self.assertEqual(extract_consent_action_id("<html></html>"), SUBMIT_OAUTH2_CONSENT_ACTION)


class OAuthPersistenceTests(unittest.TestCase):
    @patch.object(xai_oauth, "save_oauth_record")
    @patch.object(xai_oauth, "fetch_userinfo", return_value={"email": "test@example.com"})
    @patch.object(
        xai_oauth,
        "exchange_code_for_token",
        return_value={"access_token": "access", "refresh_token": "refresh"},
    )
    def test_finalize_can_skip_local_token_file(
        self,
        exchange_mock,
        userinfo_mock,
        save_mock,
    ) -> None:
        result = xai_oauth._finalize_oauth_code(
            code="authorization-code",
            code_verifier="verifier",
            redirect_uri="http://127.0.0.1:12345/callback",
            client_id="client-id",
            persist=False,
        )

        exchange_mock.assert_called_once()
        userinfo_mock.assert_called_once_with("access", proxy="")
        save_mock.assert_not_called()
        self.assertIsNone(result.path)
        self.assertEqual(result.access_token, "access")


if __name__ == "__main__":
    unittest.main()
