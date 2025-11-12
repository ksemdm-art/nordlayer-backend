"""
Alerting system for critical errors and performance issues.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import aiohttp
import smtplib
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart

from app.core.logging_config import get_logger, log_error
from app.core.config import settings

logger = get_logger("alerting")

class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of alerts."""
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    SYSTEM_RESOURCE = "system_resource"
    APPLICATION_ERROR = "application_error"
    HEALTH_CHECK = "health_check"

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertRule:
    """Base class for alert rules."""
    
    def __init__(self, name: str, severity: AlertSeverity, 
                 threshold: float, window_minutes: int = 5):
        self.name = name
        self.severity = severity
        self.threshold = threshold
        self.window_minutes = window_minutes
        self.last_triggered = None
        self.cooldown_minutes = 15  # Prevent spam
    
    def should_trigger(self, value: float) -> bool:
        """Check if alert should be triggered."""
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False
        
        return self._evaluate_condition(value)
    
    def _evaluate_condition(self, value: float) -> bool:
        """Override in subclasses to implement specific conditions."""
        raise NotImplementedError
    
    def trigger(self):
        """Mark rule as triggered."""
        self.last_triggered = datetime.utcnow()

class ErrorRateRule(AlertRule):
    """Alert rule for high error rates."""
    
    def _evaluate_condition(self, error_rate: float) -> bool:
        return error_rate > self.threshold

class ResponseTimeRule(AlertRule):
    """Alert rule for high response times."""
    
    def _evaluate_condition(self, avg_response_time: float) -> bool:
        return avg_response_time > self.threshold

class SystemResourceRule(AlertRule):
    """Alert rule for system resource usage."""
    
    def _evaluate_condition(self, usage_percent: float) -> bool:
        return usage_percent > self.threshold

class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.notification_channels: List[Callable] = []
        
        # Initialize default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alert rules."""
        self.rules = [
            ErrorRateRule("High Error Rate", AlertSeverity.HIGH, 0.05),  # 5% error rate
            ErrorRateRule("Critical Error Rate", AlertSeverity.CRITICAL, 0.10),  # 10% error rate
            ResponseTimeRule("Slow Response Time", AlertSeverity.MEDIUM, 2000),  # 2 seconds
            ResponseTimeRule("Very Slow Response Time", AlertSeverity.HIGH, 5000),  # 5 seconds
            SystemResourceRule("High CPU Usage", AlertSeverity.MEDIUM, 80),  # 80% CPU
            SystemResourceRule("Critical CPU Usage", AlertSeverity.HIGH, 95),  # 95% CPU
            SystemResourceRule("High Memory Usage", AlertSeverity.MEDIUM, 85),  # 85% Memory
            SystemResourceRule("Critical Memory Usage", AlertSeverity.HIGH, 95),  # 95% Memory
        ]
    
    def add_notification_channel(self, channel: Callable):
        """Add a notification channel."""
        self.notification_channels.append(channel)
    
    def record_metric(self, metric_name: str, value: float):
        """Record a metric value for monitoring."""
        self.metrics_buffer[metric_name].append({
            'value': value,
            'timestamp': datetime.utcnow()
        })
    
    async def check_rules(self):
        """Check all rules against current metrics."""
        current_time = datetime.utcnow()
        
        # Calculate metrics for rule evaluation
        metrics = self._calculate_metrics()
        
        for rule in self.rules:
            metric_key = self._get_metric_key_for_rule(rule)
            if metric_key in metrics:
                value = metrics[metric_key]
                
                if rule.should_trigger(value):
                    await self._trigger_alert(rule, value, current_time)
    
    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate metrics from buffered data."""
        metrics = {}
        current_time = datetime.utcnow()
        window = timedelta(minutes=5)
        
        # Error rate calculation
        error_count = 0
        total_count = 0
        
        for entry in self.metrics_buffer.get('http_requests', []):
            if current_time - entry['timestamp'] <= window:
                total_count += 1
                if entry.get('status_code', 200) >= 400:
                    error_count += 1
        
        if total_count > 0:
            metrics['error_rate'] = error_count / total_count
        
        # Response time calculation
        response_times = []
        for entry in self.metrics_buffer.get('response_times', []):
            if current_time - entry['timestamp'] <= window:
                response_times.append(entry['value'])
        
        if response_times:
            metrics['avg_response_time'] = sum(response_times) / len(response_times)
        
        # System metrics (latest values)
        for metric in ['cpu_usage', 'memory_usage', 'disk_usage']:
            buffer = self.metrics_buffer.get(metric, [])
            if buffer:
                metrics[metric] = buffer[-1]['value']
        
        return metrics
    
    def _get_metric_key_for_rule(self, rule: AlertRule) -> str:
        """Get the metric key for a specific rule."""
        if isinstance(rule, ErrorRateRule):
            return 'error_rate'
        elif isinstance(rule, ResponseTimeRule):
            return 'avg_response_time'
        elif isinstance(rule, SystemResourceRule):
            if 'CPU' in rule.name:
                return 'cpu_usage'
            elif 'Memory' in rule.name:
                return 'memory_usage'
            elif 'Disk' in rule.name:
                return 'disk_usage'
        return ''
    
    async def _trigger_alert(self, rule: AlertRule, value: float, timestamp: datetime):
        """Trigger an alert."""
        alert_id = f"{rule.name}_{int(timestamp.timestamp())}"
        
        alert = Alert(
            id=alert_id,
            type=self._get_alert_type_for_rule(rule),
            severity=rule.severity,
            title=rule.name,
            message=f"{rule.name}: {value:.2f} exceeds threshold {rule.threshold}",
            timestamp=timestamp,
            metadata={
                'rule_name': rule.name,
                'threshold': rule.threshold,
                'current_value': value,
                'metric_key': self._get_metric_key_for_rule(rule)
            }
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        rule.trigger()
        
        logger.warning(
            f"Alert triggered: {alert.title}",
            extra={
                'alert_id': alert_id,
                'severity': alert.severity.value,
                'value': value,
                'threshold': rule.threshold
            }
        )
        
        # Send notifications
        await self._send_notifications(alert)
    
    def _get_alert_type_for_rule(self, rule: AlertRule) -> AlertType:
        """Get alert type for a rule."""
        if isinstance(rule, ErrorRateRule):
            return AlertType.ERROR_RATE
        elif isinstance(rule, ResponseTimeRule):
            return AlertType.RESPONSE_TIME
        elif isinstance(rule, SystemResourceRule):
            return AlertType.SYSTEM_RESOURCE
        return AlertType.APPLICATION_ERROR
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications through all channels."""
        for channel in self.notification_channels:
            try:
                await channel(alert)
            except Exception as e:
                log_error(logger, e, {
                    'component': 'notification_channel',
                    'alert_id': alert.id
                })
    
    def resolve_alert(self, alert_id: str):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            del self.active_alerts[alert_id]
            
            logger.info(
                f"Alert resolved: {alert.title}",
                extra={'alert_id': alert_id}
            )
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """Get alert history."""
        return list(self.alert_history)[-limit:]

class TelegramNotificationChannel:
    """Telegram notification channel for alerts."""
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.session = None
    
    async def __call__(self, alert: Alert):
        """Send alert notification via Telegram."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        severity_emoji = {
            AlertSeverity.LOW: "🟡",
            AlertSeverity.MEDIUM: "🟠", 
            AlertSeverity.HIGH: "🔴",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        message = (
            f"{severity_emoji.get(alert.severity, '⚠️')} *ALERT*\n\n"
            f"*{alert.title}*\n"
            f"{alert.message}\n\n"
            f"Severity: {alert.severity.value.upper()}\n"
            f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"Alert ID: `{alert.id}`"
        )
        
        for chat_id in self.chat_ids:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                
                async with self.session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send Telegram alert: {response.status}")
                        
            except Exception as e:
                log_error(logger, e, {
                    'component': 'telegram_notification',
                    'chat_id': chat_id,
                    'alert_id': alert.id
                })

class EmailNotificationChannel:
    """Email notification channel for alerts."""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_emails: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    async def __call__(self, alert: Alert):
        """Send alert notification via email."""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Create HTML body
            html_body = f"""
            <html>
            <body>
                <h2 style="color: {'red' if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else 'orange'};">
                    Alert: {alert.title}
                </h2>
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                <p><strong>Alert ID:</strong> {alert.id}</p>
                
                <h3>Metadata:</h3>
                <ul>
                    {''.join(f'<li><strong>{k}:</strong> {v}</li>' for k, v in alert.metadata.items())}
                </ul>
            </body>
            </html>
            """
            
            msg.attach(MimeText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                
        except Exception as e:
            log_error(logger, e, {
                'component': 'email_notification',
                'alert_id': alert.id
            })

# Global alert manager instance
alert_manager = AlertManager()

async def setup_alerting():
    """Setup alerting system with notification channels."""
    
    # Setup Telegram notifications if configured
    if hasattr(settings, 'TELEGRAM_BOT_TOKEN') and hasattr(settings, 'ADMIN_CHAT_IDS'):
        telegram_channel = TelegramNotificationChannel(
            settings.TELEGRAM_BOT_TOKEN,
            settings.ADMIN_CHAT_IDS
        )
        alert_manager.add_notification_channel(telegram_channel)
    
    # Setup email notifications if configured
    if all(hasattr(settings, attr) for attr in [
        'SMTP_HOST', 'SMTP_PORT', 'SMTP_USERNAME', 
        'SMTP_PASSWORD', 'ALERT_FROM_EMAIL', 'ALERT_TO_EMAILS'
    ]):
        email_channel = EmailNotificationChannel(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.ALERT_FROM_EMAIL,
            settings.ALERT_TO_EMAILS
        )
        alert_manager.add_notification_channel(email_channel)
    
    logger.info("Alerting system configured")

async def alert_monitoring_loop():
    """Main monitoring loop for alerts."""
    while True:
        try:
            await alert_manager.check_rules()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            log_error(logger, e, {'component': 'alert_monitoring_loop'})
            await asyncio.sleep(60)