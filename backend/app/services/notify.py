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
) -> dict:
    if nudge_id in _sent_ids:
        return {"channel": "dedupe", "status": "skipped", "error": None}
    _sent_ids.add(nudge_id)

    if not twilio_enabled or not twilio_sid or not twilio_token:
        return {"channel": "fallback", "status": "sent", "error": None}

    try:
        from twilio.rest import Client
        client = Client(twilio_sid, twilio_token)
        client.messages.create(
            body=message,
            from_=twilio_from,
            to=twilio_to,
            timeout=timeout,
        )
        return {"channel": "twilio", "status": "sent", "error": None}
    except Exception as e:
        logger.warning(f"Twilio send failed: {e}")
        return {"channel": "fallback", "status": "failed", "error": str(e)}


def reset():
    _sent_ids.clear()
