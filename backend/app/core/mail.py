"""Sends email through Resend's HTTP API (no extra library). The API key comes only from the RESEND_API_KEY environment variable.

Sending never breaks a request: a failure is logged and the caller carries on."""

import html as _html
import json
import logging
import urllib.error
import urllib.request

from app.core.config import get_settings

log = logging.getLogger("app.mail")
BUTTON = "display:inline-block;padding:12px 22px;border-radius:980px;background:#0071e3;color:#fff;text-decoration:none"


def send_email(to: str, subject: str, text: str, link: str | None = None) -> bool:
    s = get_settings()
    if not s.resend_api_key:
        # Local development: show the link in the server log so the flow can be tried without an email account.
        if s.environment != "production" and link:
            log.warning("email not sent (no RESEND_API_KEY). To: %s | %s | %s", to, subject, link)
        else:
            log.warning("email not sent (no RESEND_API_KEY). To: %s | %s", to, subject)
        return False
    html = (
        '<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;font-size:16px;line-height:1.5;color:#1d1d1f">'
        + "".join(f"<p>{_html.escape(line)}</p>" for line in text.split("\n\n"))
        + (
            f'<p><a href="{link}" style="{BUTTON}">Continue</a></p>'
            if link
            else ""
        )
        + "</div>"
    )
    body = json.dumps({"from": s.email_from, "to": [to], "subject": subject, "text": text + (f"\n\n{link}" if link else ""), "html": html}).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {s.resend_api_key}", "Content-Type": "application/json", "User-Agent": "bazar-af/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:  # noqa: S310 (fixed https URL)
            return 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        log.error("email failed: HTTP %s %s", e.code, e.read()[:200])
    except Exception as e:  # network down, timeout, etc.
        log.error("email failed: %s", e)
    return False
