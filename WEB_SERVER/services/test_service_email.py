from WEB_SERVER.services.service_email import EmailService


class DummySMTP:
    sent_messages = []

    def __init__(self, server: str, port: int):
        self.server = server
        self.port = port
        self.logged_in = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        return None

    def login(self, user: str, password: str):
        self.logged_in = (user, password)

    def send_message(self, msg):
        self.sent_messages.append(msg)


def test_verification_email_builds_and_sends(monkeypatch):
    DummySMTP.sent_messages = []
    monkeypatch.setattr("WEB_SERVER.services.service_email.smtplib.SMTP", DummySMTP)

    service = EmailService(
        server="smtp.example.test",
        port=587,
        user="smtp-user",
        password="smtp-password",
        sender="no-reply@example.test",
    )

    result = service.set_verification_email(
        receiver_email="user@example.test",
        receiver_name="Test User",
        verification_token="token-123",
        service_url="https://example.test",
    ).send()

    assert result is True
    assert len(DummySMTP.sent_messages) == 1
    assert DummySMTP.sent_messages[0]["To"] == "user@example.test"
