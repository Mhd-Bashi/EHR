from flask_mail import Mail, Message

mail = Mail()


def init_mail(app):
    mail.init_app(app)


def send_email(subject: str, recipients: list[str], html: str):
    msg = Message(subject=subject, recipients=recipients, html=html)
    mail.send(msg)
