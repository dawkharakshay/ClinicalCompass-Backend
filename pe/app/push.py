"""Push delivery via Firebase Cloud Messaging (legacy HTTP API).

When ``FCM_SERVER_KEY`` is unset the sender runs in **stub mode**: it logs each
intended delivery and reports zero sent, mirroring the original Supabase edge
function which was itself a stub. Wire up the key to deliver for real.
"""

import logging

import httpx

from app import config

logger = logging.getLogger("pe.push")

FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"


def send_to_tokens(
    tokens: list[str], title: str, body: str, data: dict | None = None
) -> int:
    """Deliver one notification to many device tokens. Returns the number sent."""
    if not tokens:
        return 0

    if not config.FCM_SERVER_KEY:
        logger.info(
            "[push:stub] FCM_SERVER_KEY unset — would send '%s' to %d token(s)",
            title,
            len(tokens),
        )
        return 0

    headers = {
        "Authorization": f"key={config.FCM_SERVER_KEY}",
        "Content-Type": "application/json",
    }
    sent = 0
    with httpx.Client(timeout=10.0) as client:
        for token in tokens:
            payload = {
                "to": token,
                "notification": {"title": title, "body": body},
                "data": data or {},
            }
            try:
                resp = client.post(FCM_ENDPOINT, headers=headers, json=payload)
                if resp.status_code == 200 and resp.json().get("success", 0) == 1:
                    sent += 1
                else:
                    logger.warning(
                        "[push] FCM rejected token: %s %s", resp.status_code, resp.text[:200]
                    )
            except httpx.HTTPError as exc:
                logger.warning("[push] FCM request failed: %s", exc)
    return sent
