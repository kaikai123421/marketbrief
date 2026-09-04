"""QQ SMTP delivery for generated MarketBrief JSON reports."""

from __future__ import annotations

import html
import json
import logging
import pathlib
import smtplib
import ssl
from typing import TYPE_CHECKING
from email.message import EmailMessage

if TYPE_CHECKING:
    from marketbrief.core.config import MarketBriefConfig

log = logging.getLogger("marketbrief")


def _report_parts(report_path: str) -> tuple[str, str, str]:
    payload = json.loads(pathlib.Path(report_path).read_text(encoding="utf-8"))
    report = payload.get("report") or {}
    tagline = report.get("tagline") or "美股市场晨报"
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    escaped = html.escape(text).replace("\n", "<br>\n")
    body = f"<h1>{html.escape(tagline)}</h1><p>数据版 MarketBrief 晨报</p><pre>{escaped}</pre>"
    return tagline, text, body


def push_report(cfg: MarketBriefConfig, report_path: str | None = None):
    """Send the latest JSON report through QQ SMTP STARTTLS."""
    if not cfg.has_email:
        raise RuntimeError("QQ email is not configured")
    path = report_path or "reports/latest.json"
    tagline, text_body, html_body = _report_parts(path)

    message = EmailMessage()
    message["Subject"] = f"美股监控晨报 | {tagline}"
    message["From"] = cfg.qq_email
    message["To"] = cfg.report_recipient
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.qq.com", 587, timeout=30) as server:
        server.starttls(context=context)
        server.login(cfg.qq_email, cfg.qq_auth_code)
        server.send_message(message)
    log.info("QQ email report sent to configured recipient")
