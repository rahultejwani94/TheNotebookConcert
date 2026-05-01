import smtplib
from email.message import EmailMessage
from typing import List, Tuple

import requests
import streamlit as st


Attachment = Tuple[str, bytes]


def send_ticket_email(
    recipient_email: str,
    customer_name: str,
    booking_id: str,
    ticket_count: int,
    total_amount: str,
    attachments: List[Attachment],
) -> Tuple[bool, str]:
    """Send ticket QR attachments through SMTP when configured."""
    smtp_host = st.secrets.get("smtp_host")
    smtp_username = st.secrets.get("smtp_username")
    smtp_password = st.secrets.get("smtp_password")
    from_email = st.secrets.get("smtp_from_email", smtp_username)

    if not smtp_host or not smtp_username or not smtp_password or not from_email:
        return False, "Email delivery is not configured."

    smtp_port = int(st.secrets.get("smtp_port", 587))
    from_name = st.secrets.get("smtp_from_name", "The Notebook Concert")
    use_tls = bool(st.secrets.get("smtp_use_tls", True))

    message = EmailMessage()
    message["Subject"] = f"Your The Notebook Concert ticket{'s' if ticket_count > 1 else ''}"
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = recipient_email
    message.set_content(
        f"""Hi {customer_name},

Your booking has been received.

Booking ID: {booking_id}
Tickets: {ticket_count}
Amount paid: Rs. {total_amount}

Your ticket QR code{'s are' if ticket_count > 1 else ' is'} attached to this email.
Please keep this email available for entry verification.

The Notebook Concert
"""
    )

    for filename, content in attachments:
        message.add_attachment(content, maintype="image", subtype="png", filename=filename)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        return True, "Ticket email sent."
    except Exception as exc:
        return False, f"Email delivery failed: {exc}"


def send_ticket_whatsapp(
    recipient_phone: str,
    customer_name: str,
    booking_id: str,
    ticket_count: int,
    attachments: List[Attachment],
) -> Tuple[bool, str]:
    """Send ticket QR images through WhatsApp Cloud API when configured."""
    access_token = st.secrets.get("whatsapp_access_token")
    phone_number_id = st.secrets.get("whatsapp_phone_number_id")

    if not access_token or not phone_number_id:
        return False, "WhatsApp delivery is not configured."

    recipient = "".join(ch for ch in recipient_phone if ch.isdigit())
    if len(recipient) == 10:
        recipient = f"91{recipient}"

    api_version = st.secrets.get("whatsapp_api_version", "v20.0")
    base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        for index, (filename, content) in enumerate(attachments, start=1):
            media_response = requests.post(
                f"{base_url}/media",
                headers=headers,
                files={"file": (filename, content, "image/png")},
                data={"messaging_product": "whatsapp", "type": "image/png"},
                timeout=30,
            )
            media_response.raise_for_status()
            media_id = media_response.json()["id"]

            caption = (
                f"Hi {customer_name}, here is ticket {index}/{ticket_count} "
                f"for The Notebook Concert. Booking ID: {booking_id}"
            )
            message_response = requests.post(
                f"{base_url}/messages",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": recipient,
                    "type": "image",
                    "image": {"id": media_id, "caption": caption},
                },
                timeout=30,
            )
            message_response.raise_for_status()

        return True, "Ticket WhatsApp message sent."
    except Exception as exc:
        return False, f"WhatsApp delivery failed: {exc}"
