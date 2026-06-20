from loguru import logger
from app.core.config import settings


async def send_welcome_email(email: str, name: str) -> None:
    if not settings.RESEND_API_KEY:
        logger.info(f"Email skipped (no API key): welcome to {email}")
        return
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": email,
            "subject": "Welcome to SlashSure",
            "html": f"""
            <h2>Welcome to SlashSure, {name or 'Validator'}!</h2>
            <p>Your account has been created. Your blockchain wallet has been generated and
            is securely stored.</p>
            <p>You can export your private key from Settings → Wallet at any time.</p>
            <br/>
            <p>The SlashSure Team</p>
            """,
        })
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")


async def send_alert_email(email: str, subject: str, body: str) -> None:
    if not settings.RESEND_API_KEY:
        logger.info(f"Alert email skipped: {subject}")
        return
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": email,
            "subject": f"[SlashSure Alert] {subject}",
            "html": f"<pre>{body}</pre>",
        })
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")


async def send_slack_alert(message: str, channel: str = None) -> None:
    if not settings.SLACK_BOT_TOKEN:
        logger.info(f"Slack alert skipped: {message[:80]}")
        return
    try:
        from slack_sdk.web.async_client import AsyncWebClient
        client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
        await client.chat_postMessage(
            channel=channel or settings.SLACK_DEFAULT_CHANNEL,
            text=message,
        )
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
