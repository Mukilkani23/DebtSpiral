"""
Notification adapter: Twilio WhatsApp or fallback.
Called ONLY from BackgroundTask — never blocks the response.
"""

import logging

logger = logging.getLogger(__name__)

_sent_ids: set[str] = set()


def send(
    nudge_id: str,
    message: str,
    twilio_enabled: bool = False,
    twilio_sid: str = "",
    twilio_token: str = "",
    twilio_from: str = "",
    twilio_to: str = "",
    timeout: float = 3.0,
    twilio_api_key_sid: str = "",
    twilio_api_key_secret: str = "",
    twilio_content_sid: str = "",
) -> dict:
    """
    Auth: if twilio_api_key_sid/secret are set, authenticates as an API Key
    (Client(api_key_sid, api_key_secret, account_sid) — twilio_sid is the
    Account SID for account context). Otherwise falls back to the classic
    Account SID + Auth Token pair (twilio_sid, twilio_token).

    Delivery: if twilio_content_sid is set, sends via that pre-approved
    WhatsApp Content Template (required for approved Business senders
    outside a user-initiated session window) instead of a free-form body.
    """
    if nudge_id in _sent_ids:
        return {"channel": "dedupe", "status": "skipped", "error": None}
    _sent_ids.add(nudge_id)

    using_api_key = bool(twilio_api_key_sid and twilio_api_key_secret)
    if not twilio_enabled or not twilio_sid or not (twilio_token or using_api_key):
        return {"channel": "fallback", "status": "sent", "error": None}

    try:
        from twilio.rest import Client
        from twilio.http.http_client import TwilioHttpClient
        http_client = TwilioHttpClient(timeout=timeout)
        if using_api_key:
            client = Client(twilio_api_key_sid, twilio_api_key_secret, twilio_sid, http_client=http_client)
        else:
            client = Client(twilio_sid, twilio_token, http_client=http_client)

        if twilio_content_sid:
            client.messages.create(
                content_sid=twilio_content_sid,
                from_=twilio_from,
                to=twilio_to,
            )
        else:
            client.messages.create(
                body=message,
                from_=twilio_from,
                to=twilio_to,
            )
        return {"channel": "twilio", "status": "sent", "error": None}
    except Exception as e:
        logger.warning(f"Twilio send failed: {e}")
        return {"channel": "fallback", "status": "failed", "error": str(e)}


def reset():
    _sent_ids.clear()
