# Kapso Webhook Debugging Guide

**2026-07-25** · Lessons from BioMed's 3-hour webhook debugging session

## TL;DR
Kapso v2 sends webhooks in format `{"message": {...}, "conversation": {...}, "phone_number_id": "..."}` — **not** Meta's `{"entry": [{"changes": [{"value": {"messages": [...]}}]}]}`.

## Kapso Webhook Payload Formats

### Kapso v2 (production) — THIS IS WHAT YOU GET
```json
{
  "message": {
    "id": "wamid.xxx",
    "from": "27833753126",
    "type": "text",
    "text": {"body": "Hi"},
    "timestamp": "1784966014"
  },
  "conversation": {
    "id": "conv_xxx",
    "contact": {
      "profile": {"name": "Dumisani"},
      "wa_id": "27833753126"
    }
  },
  "phone_number_id": "1235032529693241",
  "is_new_conversation": false
}
```

### Batch format (rare)
```json
{
  "batch": true,
  "data": [
    {"message": {...}, "contact": {...}}
  ]
}
```

### Meta format (legacy / sandbox)
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{"from": "...", "text": {"body": "Hi"}}],
        "contacts": [{"profile": {"name": "User"}}]
      }
    }]
  }]
}
```

## Check Before Coding

### 1. Use Kapso CLI
```bash
npx kapso status                    # Check project context
npx kapso whatsapp numbers list     # List phone numbers
npx kapso whatsapp webhooks list --phone-number-id <ID>  # Check webhook config
```

### 2. Read webhook configuration
- `kind`: "kapso" or "meta" — determines payload format
- `payload_version`: "v1" or "v2"
- `events`: which events trigger webhooks (message.received, message.sent)
- `secret_key`: HMAC key (may be needed for verification)

### 3. Log raw payload FIRST
```python
payload = await request.json()
print(f"WEBHOOK_RAW: {json.dumps(payload)[:500]}", flush=True)
```
Never assume the format. Log first, parse later.

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| **API key from wrong page** | 403 error 1010 or 401 "Invalid credentials" | Get key from Kapso → Project → **API Keys** (not WhatsApp Configuration) |
| **Duplicate webhooks** | Race condition, inconsistent behavior | List with `kapso whatsapp webhooks list`, delete duplicates |
| **Logger.info() not visible** | Logs don't appear in Railway | Use `print()` with `flush=True` or `logging.warning()` |
| **Dashboard raw_payload ≠ webhook payload** | Testing wrong format | Kapso dashboard shows Meta's internal event, not the transformed webhook |
| **Testing only Meta format** | Works in tests, fails in production | Test with the ACTUAL Kapso v2 format |
| **Using phone number from different project** | API key works for one number, not another | Each phone number belongs to one Kapso project |

## BioMed's Fix (Reference)
```python
def extract_message_event(payload: dict) -> dict | None:
    # Kapso v2 format — CHECK THIS FIRST
    msg = payload.get("message")
    if isinstance(msg, dict):
        conversation = payload.get("conversation", {})
        contact = conversation.get("contact", {}) if isinstance(conversation, dict) else {}
        return _normalize_message(msg, contact)

    # Kapso v2 batch
    if payload.get("batch") and isinstance(payload.get("data"), list):
        ...

    # Meta format
    entries = payload.get("entry")
    ...
```

## Railway-Specific

- GitHub auto-deploy: connect repo in Railway Settings → `git push` triggers deploy
- `npx railway variables set KEY=value` — sets env vars
- `npx railway logs --service <ID>` — view logs
- `npx railway up --service <ID>` — manual deploy (falls back to CLI if GitHub not connected)
- `npx railway variables --service <ID>` — list all vars
- Railway captures **stderr** reliably; stdout may need `flush=True`
