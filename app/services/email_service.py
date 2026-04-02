import smtplib
from email.message import EmailMessage
import urllib.request
import urllib.parse
import urllib.error
import base64
import json
import asyncio
import httpx
from brevo import transactional_emails
from mailgun.client import Client
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod

class BaseEmailService(ABC):
    def __init__(self, from_email: Optional[str], from_name: Optional[str]):
        self.from_email = from_email or "noreply@example.com"
        self.from_name = from_name or "Support"
        self.executor = ThreadPoolExecutor(max_workers=3)

    @abstractmethod
    def _send_email_sync(self, to_email: str, subject: str, text: str, html: Optional[str] = None):
        pass

    async def send_welcome_email(self, to_email: str, username: str):
        subject = "Welcome to Our Platform!"
        text = f"Hi {username},\n\nWelcome to our platform. We're excited to have you on board!\n\nBest regards,\nThe Team"
        await asyncio.get_running_loop().run_in_executor(
            self.executor,
            self._send_email_sync,
            to_email,
            subject,
            text,
            None
        )

class MockEmailService(BaseEmailService):
    def _send_email_sync(self, to_email: str, subject: str, text: str, html: Optional[str] = None):
        print(f"MOCK EMAIL: To {to_email} | Subject: {subject}\n{text}")

class SMTPEmailService(BaseEmailService):
    def __init__(self, host: str, port: int, username: Optional[str], password: Optional[str], from_email: Optional[str], from_name: Optional[str]):
        super().__init__(from_email, from_name)
        self.host = host
        self.port = port
        self.smtp_username = username
        self.smtp_password = password

    def _send_email_sync(self, to_email: str, subject: str, text: str, html: Optional[str] = None):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        if html:
            msg.set_content("Please enable HTML to view this message.")
            msg.add_alternative(html, subtype='html')
        else:
            msg.set_content(text)

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                try:
                    server.starttls()
                except smtplib.SMTPNotSupportedError:
                    pass  # Local dev servers (e.g. MailHog) don't support STARTTLS
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            print(f"SMTP success to {to_email}")
        except Exception as e:
            print(f"SMTP failed to send email to {to_email}: {e}")

class MailgunEmailService(BaseEmailService):
    def __init__(self, domain: str, api_key: str, from_email: Optional[str], from_name: Optional[str]):
        super().__init__(from_email, from_name)
        self.domain = domain
        self.client = Client(auth=("api", api_key))

    def _send_email_sync(self, to_email: str, subject: str, text: str, html: Optional[str] = None):
        data = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": to_email,
            "subject": subject,
            "text": text
        }
        if html:
            data["html"] = html
            
        try:
            response = self.client.messages.create(data=data, domain=self.domain)
            print(f"Mailgun config dispatch to {to_email}")
        except Exception as e:
            print(f"Mailgun unexpected error to {to_email}: {e}")

class BrevoEmailService(BaseEmailService):
    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, api_key: str, from_email: Optional[str], from_name: Optional[str]):
        super().__init__(from_email, from_name)
        self.api_key = api_key

    def _send_email_sync(self, to_email: str, subject: str, text: str, html: Optional[str] = None):
        payload = transactional_emails.SendTransacEmailRequestToItem(email=to_email)
        sender = transactional_emails.SendTransacEmailRequestSender(
            name=self.from_name, email=self.from_email
        )
        body = {
            "sender": sender.model_dump(),
            "to": [payload.model_dump()],
            "subject": subject,
            "textContent": text
        }
        if html:
            body["htmlContent"] = html

        try:
            with httpx.Client() as client:
                response = client.post(
                    self.BREVO_API_URL,
                    json=body,
                    headers={"api-key": self.api_key, "Content-Type": "application/json"}
                )
                response.raise_for_status()
                print(f"Brevo success dispatch to {to_email}")
        except Exception as e:
            print(f"Brevo error to {to_email}: {e}")
