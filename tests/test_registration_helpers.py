import os
import unittest
from unittest.mock import patch

from grok2api.upstream.grok_build_adapter import (
    extract_xai_otp,
    registration_auth_flow,
)


class OtpExtractionTests(unittest.TestCase):
    def test_normalizes_hyphenated_code(self) -> None:
        self.assertEqual(extract_xai_otp({"content": "Your code is Ab1-C2d"}), "AB1C2D")

    def test_accepts_plain_code_in_xai_message(self) -> None:
        self.assertEqual(extract_xai_otp({"from": "security@x.ai", "text": "Code ZX90Q1"}), "ZX90Q1")

    def test_rejects_plain_code_without_xai_context(self) -> None:
        self.assertIsNone(extract_xai_otp({"text": "Unrelated code ZX90Q1"}))

    def test_rejects_invalid_extracted_code_and_non_mapping(self) -> None:
        self.assertIsNone(extract_xai_otp({"extracted": {"codes": ["12345", "A_B-C!"]}}))
        self.assertIsNone(extract_xai_otp({"extracted": ["ABC-123"]}))


class RegistrationAuthFlowTests(unittest.TestCase):
    def test_defaults_to_device(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(registration_auth_flow(), "device")

    def test_accepts_explicit_flows(self) -> None:
        self.assertEqual(registration_auth_flow(" DEVICE "), "device")
        self.assertEqual(registration_auth_flow("OAuth"), "oauth")

    def test_reads_oauth_from_environment(self) -> None:
        with patch.dict(os.environ, {"GROK2API_REG_AUTH_FLOW": "oauth"}, clear=True):
            self.assertEqual(registration_auth_flow(), "oauth")

    def test_rejects_unknown_flow(self) -> None:
        with self.assertRaises(ValueError):
            registration_auth_flow("automatic")


if __name__ == "__main__":
    unittest.main()
