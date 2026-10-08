"""Step 8-10 のテスト:  python -m unittest discover -s tests -v"""
import os
import sys
import unittest
from urllib.parse import quote_plus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import step8_s3_trigger as s3step  # noqa: E402
import step9_sqs_worker as sqsstep  # noqa: E402
import step10_jwt_claims as jwtstep  # noqa: E402
from _fake import FakeContext, http_event  # noqa: E402


class S3TriggerTest(unittest.TestCase):
    def setUp(self):
        s3step._s3 = s3step.FakeS3({("b", "my notes/メモ.txt"): "abc"})

    def test_decodes_url_encoded_key(self):
        key = quote_plus("my notes/メモ.txt", safe="/")
        result = s3step.handler(s3step.s3_event("b", key), FakeContext())
        self.assertEqual(result["processed"], [{"key": "my notes/メモ.txt", "chars": 3}])

    def test_skips_non_txt(self):
        result = s3step.handler(s3step.s3_event("b", "a.png"), FakeContext())
        self.assertEqual(result["processed"], [])


class SqsWorkerTest(unittest.TestCase):
    def setUp(self):
        sqsstep._done_ids.clear()

    def test_partial_batch_failure(self):
        event = sqsstep.sqs_event({"amount": 1}, {"bad": 1}, "not json")
        result = sqsstep.handler(event, FakeContext())
        failed = [f["itemIdentifier"] for f in result["batchItemFailures"]]
        self.assertEqual(failed, ["msg-1", "msg-2"])

    def test_duplicate_delivery_is_ignored(self):
        event = sqsstep.sqs_event({"amount": 1})
        sqsstep.handler(event, FakeContext())
        self.assertEqual(sqsstep.handler(event, FakeContext())["batchItemFailures"], [])


class JwtTest(unittest.TestCase):
    def call(self, event):
        return jwtstep.handler(event, FakeContext())["statusCode"]

    def test_no_authorizer_is_401(self):
        self.assertEqual(self.call(http_event("GET", "/notes")), 401)

    def test_missing_scope_is_403(self):
        self.assertEqual(self.call(jwtstep.with_jwt(http_event("GET", "/notes"), "user-a")), 403)

    def test_returns_only_own_notes(self):
        event = jwtstep.with_jwt(http_event("GET", "/notes"), "user-a", ["notes/read"])
        res = jwtstep.handler(event, FakeContext())
        self.assertEqual(res["statusCode"], 200)
        self.assertIn("a のメモ", res["body"])
        self.assertNotIn("b のメモ", res["body"])


if __name__ == "__main__":
    unittest.main()
