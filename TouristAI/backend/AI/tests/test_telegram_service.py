import os
import sys
import types
import unittest
from unittest.mock import patch


# The unit tests exercise local formatting and access-control behavior only.
# Keep importing the service independent from an installed HTTP client.
if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(post=lambda *args, **kwargs: None)

from backend.AI.services.telegram_service import (
    is_user_allowed,
    questionnaire_keyboard,
    split_message,
    verify_webhook_secret,
)


class TelegramServiceTests(unittest.TestCase):
    def test_demo_mode_requires_an_explicit_allowed_user(self):
        env = {
            "TELEGRAM_DEMO_MODE": "true",
            "TELEGRAM_ALLOWED_USER_IDS": "12345, 67890",
        }
        with patch.dict(os.environ, env, clear=False):
            self.assertTrue(is_user_allowed(12345))
            self.assertFalse(is_user_allowed(99999))

    def test_webhook_secret_is_required_and_compared(self):
        with patch.dict(os.environ, {"TELEGRAM_WEBHOOK_SECRET": "test-secret"}, clear=False):
            self.assertTrue(verify_webhook_secret("test-secret"))
            self.assertFalse(verify_webhook_secret("wrong-secret"))
            self.assertFalse(verify_webhook_secret(None))

    def test_long_messages_are_split_below_telegram_limit(self):
        chunks = split_message("Delhi itinerary " * 600, limit=500)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(0 < len(chunk) <= 500 for chunk in chunks))

    def test_questionnaire_answer_gets_inline_buttons(self):
        keyboard = questionnaire_keyboard("Which mode of travel do you prefer?")
        labels = [button["text"] for row in keyboard["inline_keyboard"] for button in row]
        self.assertEqual(labels, ["Car", "Bus", "Train", "Flight"])


if __name__ == "__main__":
    unittest.main()
