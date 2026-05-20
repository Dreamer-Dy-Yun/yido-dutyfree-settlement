###########################################
# Module name : email_message_builder.py
# Module functions : Shared email MIME message assembly helpers.
############################################

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_alternative_email_message(
    sender: str,
    receiver_email: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> MIMEMultipart:
    """Build a multipart email with plain text and HTML alternatives."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver_email

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg
