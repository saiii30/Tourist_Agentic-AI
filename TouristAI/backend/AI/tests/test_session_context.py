import contextvars
import unittest

from backend.AI.session_context import get_session_id, normalize_session_id, set_session_id


class SessionContextTests(unittest.TestCase):
    def test_normalizes_untrusted_session_identifier(self):
        self.assertEqual(normalize_session_id(" web:<bad>/id "), "web:badid")

    def test_contexts_do_not_share_session_identity(self):
        first = contextvars.copy_context()
        second = contextvars.copy_context()
        first.run(set_session_id, "web:first")
        second.run(set_session_id, "web:second")
        self.assertEqual(first.run(get_session_id), "web:first")
        self.assertEqual(second.run(get_session_id), "web:second")


if __name__ == "__main__":
    unittest.main()
