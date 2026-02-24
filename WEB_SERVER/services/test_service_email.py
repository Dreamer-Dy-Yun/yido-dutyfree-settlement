from service_email import EmailService

email_service = EmailService(
    server="smtp.gmail.com",
    port=587,
    user="yido.repository@gmail.com",
    password="uioi odyf rzgv zvil",
    sender="yido.repository@gmail.com"
)

email_service.set_verification_email(
    receiver_email="dreamer.dy.yun@gmail.com",
    receiver_name="Yun Dae-young",
    verification_token="1234567890",
    service_url="http://localhost:3001"
).send()