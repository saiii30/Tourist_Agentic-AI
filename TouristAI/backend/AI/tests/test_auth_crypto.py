import sys
import types
import unittest


# Crypto helpers do not need a database; provide a small import stub for the
# bundled test runtime, which intentionally does not ship psycopg2.
postgres_stub = types.ModuleType("backend.AI.database.postgres")
postgres_stub.PostgresDatabase = object
sys.modules.setdefault("backend.AI.database.postgres", postgres_stub)

from backend.AI.services.auth_service import hash_password, normalize_email, verify_password


class AuthCryptoTests(unittest.TestCase):
    def test_password_hash_round_trip_and_wrong_password(self):
        encoded_hash, salt, iterations = hash_password("StrongPass123")
        self.assertTrue(verify_password("StrongPass123", encoded_hash, salt, iterations))
        self.assertFalse(verify_password("WrongPass123", encoded_hash, salt, iterations))

    def test_email_is_normalized(self):
        self.assertEqual(normalize_email(" User@Example.COM "), "user@example.com")

    def test_weak_password_is_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("short")


if __name__ == "__main__":
    unittest.main()
