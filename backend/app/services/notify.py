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

    Delivery: ALWAYS attempts the real, person-specific `message` text
    first (a free-form body) — this is what makes the notification
    relative to the exact problem the caller detected, not a generic
    string. Only if WhatsApp rejects it with error 21654 ("outside the
    allowed session window" — Meta requires an approved template for a
    Business sender when the recipient hasn't messaged in the last 24h)
    does it fall back to twilio_content_sid, a pre-approved template with
    fixed text. That fallback is a last resort: the personalized text is
    NOT delivered in that case, and this is logged so it's visible, not
    silently swallowed.
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
        from twilio.base.exceptions import TwilioRestException
        http_client = TwilioHttpClient(timeout=timeout)
        if using_api_key:
            client = Client(twilio_api_key_sid, twilio_api_key_secret, twilio_sid, http_client=http_client)
        else:
            client = Client(twilio_sid, twilio_token, http_client=http_client)

        try:
            client.messages.create(body=message, from_=twilio_from, to=twilio_to)
            return {"channel": "twilio", "status": "sent", "error": None}
        except TwilioRestException as e:
            if e.code == 21654 and twilio_content_sid:
                logger.warning(
                    "No open WhatsApp session (error 21654) — falling back to "
                    "the generic Content Template; the personalized message "
                    "was NOT delivered this time."
                )
                client.messages.create(
                    content_sid=twilio_content_sid, from_=twilio_from, to=twilio_to,
                )
                return {"channel": "twilio_template_fallback", "status": "sent", "error": None}
            raise
    except Exception as e:
        logger.warning(f"Twilio send failed: {e}")
        return {"channel": "fallback", "status": "failed", "error": str(e)}


def reset():
    _sent_ids.clear()
