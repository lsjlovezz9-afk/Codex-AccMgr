from __future__ import annotations

import base64
import json


def _decode_jwt_payload(jwt_token: str) -> dict:
    parts = jwt_token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    padding = "=" * ((4 - len(payload) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded)
    except Exception:
        return {}


def parse_jwt_email(jwt_token: str) -> str:
    payload = _decode_jwt_payload(jwt_token)
    return payload.get("email", "")


def parse_jwt_plan(jwt_token: str) -> str:
    payload = _decode_jwt_payload(jwt_token)
    auth_data = payload.get("https://api.openai.com/auth", {})
    if isinstance(auth_data, dict):
        return auth_data.get("chatgpt_plan_type", "unknown")
    return "unknown"


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked = (local[:1] or "") + "**"
    else:
        masked = local[:3] + "**"
    return masked + "@" + domain
