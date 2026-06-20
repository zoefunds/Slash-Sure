"""
Email notifications via Brevo (formerly Sendinblue).
Handles: email verification, forgot password, welcome, alerts.
"""

import httpx
from loguru import logger

from app.core.config import settings

BREVO_API = "https://api.brevo.com/v3/smtp/email"


async def _send(subject: str, to_email: str, to_name: str, html: str) -> bool:
    if not settings.BREVO_API_KEY:
        logger.info("Brevo key not set — email skipped: %s → %s", subject, to_email)
        return False
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                BREVO_API,
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "sender": {
                        "name": settings.BREVO_SENDER_NAME,
                        "email": settings.BREVO_SENDER_EMAIL,
                    },
                    "to": [{"email": to_email, "name": to_name or to_email}],
                    "subject": subject,
                    "htmlContent": html,
                },
            )
            resp.raise_for_status()
            logger.info("Email sent: %s → %s", subject, to_email)
            return True
    except Exception as exc:
        logger.error("Brevo send failed (%s → %s): %s", subject, to_email, exc)
        return False


# ── Email templates ────────────────────────────────────────────────────────────

def _base_template(title: str, body: str, cta_url: str = "", cta_label: str = "") -> str:
    cta_block = f"""
    <div style="text-align:center;margin:32px 0;">
      <a href="{cta_url}"
         style="background:#388bfd;color:#ffffff;padding:14px 32px;border-radius:8px;
                text-decoration:none;font-weight:600;font-size:15px;display:inline-block;">
        {cta_label}
      </a>
    </div>
    """ if cta_url else ""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#060d1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#0d1829;border-radius:16px;border:1px solid #1e2d45;overflow:hidden;max-width:600px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#0d1829 0%,#0a1628 100%);
                     padding:32px 40px;border-bottom:1px solid #1e2d45;text-align:center;">
            <div style="font-size:24px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">
              <span style="color:#388bfd;">Slash</span>Sure
            </div>
            <div style="font-size:11px;color:#4a6080;margin-top:4px;letter-spacing:2px;text-transform:uppercase;">
              AI-Powered Slashing Protection
            </div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">
            <h2 style="color:#ffffff;font-size:22px;font-weight:700;margin:0 0 16px 0;">{title}</h2>
            <div style="color:#8899aa;font-size:15px;line-height:1.7;">
              {body}
            </div>
            {cta_block}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:24px 40px;border-top:1px solid #1e2d45;text-align:center;">
            <p style="color:#4a6080;font-size:12px;margin:0;">
              © 2025 SlashSure · AI-native trust layer for decentralised networks
            </p>
            <p style="color:#4a6080;font-size:11px;margin:8px 0 0 0;">
              If you did not request this email, please ignore it safely.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ── Public functions ───────────────────────────────────────────────────────────

async def send_verification_email(email: str, name: str, token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html = _base_template(
        title="Verify your email address",
        body=f"""
        <p>Hi {name or 'there'},</p>
        <p>Thank you for joining <strong>SlashSure</strong>. To activate your account and
        start monitoring validators, please verify your email address.</p>
        <p>This link expires in <strong>24 hours</strong>.</p>
        """,
        cta_url=verify_url,
        cta_label="Verify Email Address",
    )
    return await _send("Verify your SlashSure email", email, name, html)


async def send_welcome_email(email: str, name: str) -> bool:
    html = _base_template(
        title=f"Welcome to SlashSure, {name or 'Validator'}!",
        body=f"""
        <p>Your account is set up and your blockchain wallet has been securely generated.</p>
        <ul style="padding-left:20px;">
          <li style="margin-bottom:8px;">Monitor validators across EigenLayer, Symbiotic, Babylon, and Cosmos</li>
          <li style="margin-bottom:8px;">Get AI-powered slashing risk scores in real time</li>
          <li style="margin-bottom:8px;">File and track insurance claims with on-chain adjudication</li>
        </ul>
        <p>Export your wallet private key any time from <strong>Settings → Wallet</strong>.</p>
        """,
        cta_url=f"{settings.FRONTEND_URL}/dashboard",
        cta_label="Go to Dashboard",
    )
    return await _send("Welcome to SlashSure 🛡", email, name, html)


async def send_forgot_password_email(email: str, name: str, token: str) -> bool:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = _base_template(
        title="Reset your password",
        body=f"""
        <p>Hi {name or 'there'},</p>
        <p>We received a request to reset the password for your SlashSure account.</p>
        <p>Click the button below to choose a new password. This link expires in
        <strong>1 hour</strong>.</p>
        <p style="color:#ef4444;font-size:13px;">
          ⚠ If you did not request a password reset, your account may be at risk.
          Please contact support immediately.
        </p>
        """,
        cta_url=reset_url,
        cta_label="Reset Password",
    )
    return await _send("Reset your SlashSure password", email, name, html)


async def send_password_changed_email(email: str, name: str) -> bool:
    html = _base_template(
        title="Your password was changed",
        body=f"""
        <p>Hi {name or 'there'},</p>
        <p>Your SlashSure account password was successfully changed.</p>
        <p style="color:#ef4444;font-size:13px;">
          ⚠ If you did not make this change, contact support immediately and secure your account.
        </p>
        """,
        cta_url=f"{settings.FRONTEND_URL}/dashboard",
        cta_label="Go to Dashboard",
    )
    return await _send("Your password was changed", email, name, html)


async def send_slash_alert_email(
    email: str,
    name: str,
    operator_name: str,
    network: str,
    fault_probability: int,
    recommended_action: str,
    case_id: str,
) -> bool:
    severity_color = "#ef4444" if fault_probability >= 70 else "#f59e0b" if fault_probability >= 40 else "#22c55e"
    html = _base_template(
        title=f"🚨 Slashing Alert: {operator_name}",
        body=f"""
        <p>Hi {name or 'there'},</p>
        <p>SlashSure has detected a potential slashing event requiring your attention.</p>
        <table style="width:100%;background:#0a1628;border-radius:8px;padding:16px;margin:16px 0;border:1px solid #1e2d45;">
          <tr><td style="color:#4a6080;font-size:13px;padding:6px 0;">Operator</td>
              <td style="color:#ffffff;font-weight:600;padding:6px 0;">{operator_name}</td></tr>
          <tr><td style="color:#4a6080;font-size:13px;padding:6px 0;">Network</td>
              <td style="color:#ffffff;padding:6px 0;">{network}</td></tr>
          <tr><td style="color:#4a6080;font-size:13px;padding:6px 0;">Fault Probability</td>
              <td style="color:{severity_color};font-weight:700;padding:6px 0;">{fault_probability}%</td></tr>
          <tr><td style="color:#4a6080;font-size:13px;padding:6px 0;">AI Recommendation</td>
              <td style="color:#ffffff;padding:6px 0;">{recommended_action.replace('_',' ').title()}</td></tr>
        </table>
        """,
        cta_url=f"{settings.FRONTEND_URL}/dashboard/slashing/{case_id}",
        cta_label="Review Case",
    )
    return await _send(f"[SlashSure] Slashing Alert — {operator_name} ({network})", email, name, html)


async def send_claim_adjudicated_email(
    email: str,
    name: str,
    claim_number: str,
    status: str,
    approved_amount: float,
) -> bool:
    status_color = "#22c55e" if status == "approved" else "#ef4444" if status == "rejected" else "#f59e0b"
    html = _base_template(
        title=f"Claim {claim_number} — {status.title()}",
        body=f"""
        <p>Hi {name or 'there'},</p>
        <p>Your insurance claim has been adjudicated by SlashSure's AI on GenLayer.</p>
        <table style="width:100%;background:#0a1628;border-radius:8px;padding:16px;margin:16px 0;border:1px solid #1e2d45;">
          <tr><td style="color:#4a6080;font-size:13px;padding:6px 0;">Claim Number</td>
              <td style="color:#ffffff;font-weight:600;padding:6px 0;">{claim_number}</td></tr>
          <tr><td style="color:#4a6080;font-size:13px;padding:6px 0;">Status</td>
              <td style="color:{status_color};font-weight:700;padding:6px 0;">{status.title()}</td></tr>
          <tr><td style="color:#4a6080;font-size:13px;padding:6px 0;">Approved Amount</td>
              <td style="color:#22c55e;font-weight:700;padding:6px 0;">{approved_amount} GEN</td></tr>
        </table>
        """,
        cta_url=f"{settings.FRONTEND_URL}/dashboard/insurance",
        cta_label="View Claim",
    )
    return await _send(f"[SlashSure] Claim {claim_number} {status.title()}", email, name, html)
