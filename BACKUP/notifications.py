"""
Notification Module
Send alerts via Telegram, Email, or other channels
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime
from config import (
    ENABLE_NOTIFICATIONS,
    NOTIFICATION_METHODS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    EMAIL_FROM,
    EMAIL_TO,
    EMAIL_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT
)


class NotificationManager:
    """
    Manages notifications across multiple channels
    """
    def __init__(self):
        self.enabled = ENABLE_NOTIFICATIONS
        self.methods = NOTIFICATION_METHODS
        
        if self.enabled:
            print(f"📢 Notifications enabled: {', '.join(self.methods)}")
    
    def send(self, title, message, level="INFO"):
        """
        Send notification via all enabled methods
        
        Args:
            title: Notification title
            message: Notification message
            level: "INFO", "WARNING", "ERROR", "TRADE"
        """
        if not self.enabled:
            return
        
        # Add timestamp and emoji
        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "🚨",
            "TRADE": "💰"
        }
        
        emoji = emoji_map.get(level, "📬")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted_title = f"{emoji} {title}"
        formatted_message = f"[{timestamp}]\n\n{message}"
        
        # Send via each enabled method
        if "telegram" in self.methods:
            self._send_telegram(formatted_title, formatted_message)
        
        if "email" in self.methods:
            self._send_email(formatted_title, formatted_message)
        
        if "discord" in self.methods:
            self._send_discord(formatted_title, formatted_message)
    
    def _send_telegram(self, title, message):
        """Send notification via Telegram"""
        try:
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                print("⚠️ Telegram credentials not configured")
                return
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            full_message = f"<b>{title}</b>\n\n{message}"
            
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": full_message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✅ Telegram notification sent")
            else:
                print(f"⚠️ Telegram error: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Telegram notification failed: {e}")
    
    def _send_email(self, title, message):
        """Send notification via Email"""
        try:
            if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASSWORD:
                print("⚠️ Email credentials not configured")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO
            msg['Subject'] = title
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send via SMTP
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                server.send_message(msg)
            
            print("✅ Email notification sent")
        
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
    
    def _send_discord(self, title, message):
        """Send notification via Discord webhook"""
        # Implement Discord webhook if needed
        print("⚠️ Discord notifications not yet implemented")
    
    def trade_opened(self, direction, entry, sl, tp, lot_size):
        """Send notification when trade is opened"""
        message = f"""
Trade Opened: {direction}

Entry: {entry:.5f}
Stop Loss: {sl:.5f}
Take Profit: {tp:.5f}
Position Size: {lot_size} lots

Risk-Reward: {abs(tp - entry) / abs(entry - sl):.2f}
        """
        
        self.send("Trade Opened", message.strip(), "TRADE")
    
    def trade_closed(self, direction, entry, exit_price, pnl):
        """Send notification when trade is closed"""
        outcome = "WIN ✅" if pnl > 0 else "LOSS ❌" if pnl < 0 else "BREAKEVEN"
        
        message = f"""
Trade Closed: {direction} - {outcome}

Entry: {entry:.5f}
Exit: {exit_price:.5f}
Profit/Loss: ${pnl:.2f}
        """
        
        level = "TRADE" if pnl >= 0 else "WARNING"
        self.send("Trade Closed", message.strip(), level)
    
    def daily_summary(self, stats):
        """Send daily performance summary"""
        message = f"""
Daily Trading Summary

Trades: {stats['trades']}
Wins: {stats['wins']} | Losses: {stats['losses']}
PnL: ${stats['pnl']:.2f}
Win Rate: {(stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0:.1f}%
        """
        
        self.send("Daily Summary", message.strip(), "INFO")
    
    def risk_alert(self, alert_type, details):
        """Send risk management alert"""
        message = f"""
Risk Alert: {alert_type}

{details}
        """
        
        self.send("Risk Alert", message.strip(), "WARNING")
    
    def error_alert(self, error_message):
        """Send error notification"""
        message = f"""
System Error Detected

{error_message}

Please check the system immediately.
        """
        
        self.send("System Error", message.strip(), "ERROR")
    
    def kill_switch_activated(self, reason):
        """Send kill switch activation alert"""
        message = f"""
🚨 KILL SWITCH ACTIVATED 🚨

Reason: {reason}

All trading has been halted.
Please investigate and resolve the issue.
        """
        
        self.send("KILL SWITCH ACTIVATED", message.strip(), "ERROR")


# Global notification manager instance
notifier = NotificationManager()


# Convenience functions
def notify_trade_opened(direction, entry, sl, tp, lot_size):
    """Shortcut to send trade opened notification"""
    notifier.trade_opened(direction, entry, sl, tp, lot_size)


def notify_trade_closed(direction, entry, exit_price, pnl):
    """Shortcut to send trade closed notification"""
    notifier.trade_closed(direction, entry, exit_price, pnl)


def notify_error(error_message):
    """Shortcut to send error notification"""
    notifier.error_alert(error_message)


def notify_daily_summary(stats):
    """Shortcut to send daily summary"""
    notifier.daily_summary(stats)


def notify_risk_alert(alert_type, details):
    """Shortcut to send risk alert"""
    notifier.risk_alert(alert_type, details)


def notify_kill_switch(reason):
    """Shortcut to send kill switch alert"""
    notifier.kill_switch_activated(reason)


# Test function
if __name__ == "__main__":
    print("Testing notification system...")
    
    # Test info message
    notifier.send("Test Notification", "This is a test message", "INFO")
    
    # Test trade notification
    notifier.trade_opened("LONG", 1.12345, 1.12000, 1.13000, 0.10)
