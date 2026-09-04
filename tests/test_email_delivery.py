import unittest
from types import SimpleNamespace
from unittest.mock import patch

from marketbrief.delivery.email import push_report


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in = None
        self.sent = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def starttls(self, context=None):
        self.started_tls = True

    def login(self, username, password):
        self.logged_in = (username, password)

    def send_message(self, message):
        self.sent = message


class EmailDeliveryTests(unittest.TestCase):
    def test_push_report_sends_html_through_qq_starttls(self):
        report = self._tmp_report()
        cfg = SimpleNamespace(
            qq_email="sender@qq.com",
            qq_auth_code="authorization-code",
            report_recipient="reader@example.com",
            has_email=True,
        )
        FakeSMTP.instances.clear()

        with patch("marketbrief.delivery.email.smtplib.SMTP", FakeSMTP):
            push_report(cfg, str(report))

        smtp = FakeSMTP.instances[0]
        self.assertEqual((smtp.host, smtp.port), ("smtp.qq.com", 587))
        self.assertTrue(smtp.started_tls)
        self.assertEqual(smtp.logged_in, ("sender@qq.com", "authorization-code"))
        self.assertEqual(smtp.sent["To"], "reader@example.com")
        self.assertEqual(smtp.sent.get_content_type(), "multipart/alternative")

    @staticmethod
    def _tmp_report():
        import tempfile
        from pathlib import Path

        path = Path(tempfile.mkstemp(suffix=".json")[1])
        path.write_text(
        '{"report": {"tagline": "测试晨报"}, "generated_at": "2026-09-05T00:00:00+00:00"}',
        encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    unittest.main()
