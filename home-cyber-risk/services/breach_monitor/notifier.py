"""Notifier component for sending breach alerts."""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Notifier(ABC):
    """Abstract base class for notifiers."""
    
    @abstractmethod
    def send_alert(self, breaches: List[Dict[str, Any]], identifier: str) -> bool:
        """
        Send alert for breaches.
        
        Args:
            breaches: List of breach dictionaries
            identifier: Identifier that was breached
        
        Returns:
            True if alert sent successfully
        """
        pass


class LogNotifier(Notifier):
    """Log-based notifier (always enabled, fallback)."""
    
    def send_alert(self, breaches: List[Dict[str, Any]], identifier: str) -> bool:
        """Log breach alerts."""
        logger.warning(f"BREACH ALERT: {len(breaches)} breach(es) detected for {identifier}")
        for breach in breaches:
            logger.warning(
                f"  - Breach: {breach['breach_name']}, "
                f"Date: {breach.get('breach_date')}, "
                f"Data Classes: {breach.get('data_classes', [])}"
            )
        return True


class EmailNotifier(Notifier):
    """Email notifier using SMTP."""
    
    def __init__(self):
        """Initialize email notifier from environment variables."""
        self.enabled = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
        self.smtp_host = os.getenv("ALERT_EMAIL_SMTP_HOST")
        self.smtp_port = int(os.getenv("ALERT_EMAIL_SMTP_PORT", "587"))
        self.smtp_user = os.getenv("ALERT_EMAIL_SMTP_USER")
        self.smtp_password = os.getenv("ALERT_EMAIL_SMTP_PASSWORD")
        self.from_addr = os.getenv("ALERT_EMAIL_FROM")
        self.to_addr = os.getenv("ALERT_EMAIL_TO")
        self.use_tls = os.getenv("ALERT_EMAIL_USE_TLS", "true").lower() == "true"
    
    def send_alert(self, breaches: List[Dict[str, Any]], identifier: str) -> bool:
        """Send email alert."""
        if not self.enabled:
            return False
        
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.from_addr, self.to_addr]):
            logger.warning("Email notifier enabled but missing configuration")
            return False
        
        try:
            subject = f"Breach Alert: {len(breaches)} breach(es) detected for {identifier}"
            body = self._format_email_body(breaches, identifier)
            
            # Send email asynchronously
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # If loop is running, schedule coroutine
                asyncio.create_task(self._send_email_async(subject, body))
            else:
                # If loop not running, run it
                loop.run_until_complete(self._send_email_async(subject, body))
            
            logger.info(f"Email alert sent for {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def _send_email_async(self, subject: str, body: str):
        """Send email asynchronously."""
        import aiosmtplib
        from email.message import EmailMessage
        
        message = EmailMessage()
        message["From"] = self.from_addr
        message["To"] = self.to_addr
        message["Subject"] = subject
        message.set_content(body)
        
        smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port)
        await smtp.connect()
        if self.use_tls:
            await smtp.starttls()
        await smtp.login(self.smtp_user, self.smtp_password)
        await smtp.send_message(message)
        await smtp.quit()
    
    def _format_email_body(self, breaches: List[Dict[str, Any]], identifier: str) -> str:
        """Format email body."""
        body = f"Breach Alert for {identifier}\n\n"
        body += f"Found {len(breaches)} breach(es):\n\n"
        
        for i, breach in enumerate(breaches, 1):
            body += f"{i}. {breach['breach_name']}\n"
            if breach.get('breach_date'):
                body += f"   Date: {breach['breach_date']}\n"
            if breach.get('data_classes'):
                body += f"   Data Exposed: {', '.join(breach['data_classes'])}\n"
            if breach.get('description'):
                body += f"   Description: {breach['description'][:200]}\n"
            body += "\n"
        
        body += "\nRecommended Actions:\n"
        body += "- Change passwords for affected services\n"
        body += "- Enable two-factor authentication where available\n"
        body += "- Review account activity for suspicious behavior\n"
        body += "- Consider using a password manager\n"
        
        return body


class TelegramNotifier(Notifier):
    """Telegram bot notifier."""
    
    def __init__(self):
        """Initialize Telegram notifier from environment variables."""
        self.enabled = os.getenv("ALERT_TELEGRAM_ENABLED", "false").lower() == "true"
        self.bot_token = os.getenv("ALERT_TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("ALERT_TELEGRAM_CHAT_ID")
    
    def send_alert(self, breaches: List[Dict[str, Any]], identifier: str) -> bool:
        """Send Telegram alert."""
        if not self.enabled:
            return False
        
        if not all([self.bot_token, self.chat_id]):
            logger.warning("Telegram notifier enabled but missing configuration")
            return False
        
        try:
            import requests
            
            message = self._format_telegram_message(breaches, identifier)
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            response = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            })
            
            if response.status_code == 200:
                logger.info(f"Telegram alert sent for {identifier}")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def _format_telegram_message(self, breaches: List[Dict[str, Any]], identifier: str) -> str:
        """Format Telegram message."""
        message = f"*Breach Alert*\n\n"
        message += f"Found {len(breaches)} breach(es) for `{identifier}`\n\n"
        
        for i, breach in enumerate(breaches, 1):
            message += f"*{i}. {breach['breach_name']}*\n"
            if breach.get('breach_date'):
                message += f"Date: {breach['breach_date']}\n"
            if breach.get('data_classes'):
                message += f"Data: {', '.join(breach['data_classes'])}\n"
            message += "\n"
        
        message += "\n*Actions:*\n"
        message += "- Change passwords\n"
        message += "- Enable 2FA\n"
        message += "- Review account activity\n"
        
        return message


class WebhookNotifier(Notifier):
    """Webhook notifier for local integrations."""
    
    def __init__(self):
        """Initialize webhook notifier from environment variables."""
        self.enabled = os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true"
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    
    def send_alert(self, breaches: List[Dict[str, Any]], identifier: str) -> bool:
        """Send webhook alert."""
        if not self.enabled:
            return False
        
        if not self.webhook_url:
            logger.warning("Webhook notifier enabled but missing URL")
            return False
        
        try:
            import requests
            
            payload = {
                "identifier": identifier,
                "breach_count": len(breaches),
                "breaches": breaches,
                "timestamp": str(datetime.now())
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Webhook alert sent for {identifier}")
                return True
            else:
                logger.error(f"Webhook error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


class NotifierManager:
    """Manages multiple notifiers."""
    
    def __init__(self):
        """Initialize notifier manager with all available notifiers."""
        self.notifiers = [
            LogNotifier(),  # Always enabled
            EmailNotifier(),
            TelegramNotifier(),
            WebhookNotifier()
        ]
    
    def send_alert(self, breaches: List[Dict[str, Any]], identifier: str) -> Dict[str, bool]:
        """
        Send alerts via all enabled notifiers.
        
        Args:
            breaches: List of breach dictionaries
            identifier: Identifier that was breached
        
        Returns:
            Dictionary mapping notifier names to success status
        """
        results = {}
        
        for notifier in self.notifiers:
            notifier_name = notifier.__class__.__name__
            try:
                success = notifier.send_alert(breaches, identifier)
                results[notifier_name] = success
            except Exception as e:
                logger.error(f"Error in {notifier_name}: {e}")
                results[notifier_name] = False
        
        return results

