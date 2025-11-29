"""
Notification Manager - Handles sending notifications to various services
Supports: Webhook, Discord, Slack, Telegram, Email, Ntfy, Gotify, Pushover
"""

import asyncio
import logging
import aiohttp
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum

from app.config.config_manager import config_manager, AutoHealEvent

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notification services"""
    WEBHOOK = "webhook"
    DISCORD = "discord"
    SLACK = "slack"
    TELEGRAM = "telegram"
    EMAIL = "email"
    NTFY = "ntfy"
    GOTIFY = "gotify"
    PUSHOVER = "pushover"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationManager:
    """
    Manages notification delivery to various services
    """

    def __init__(self):
        """Initialize notification manager"""
        self._session: Optional[aiohttp.ClientSession] = None
        self._notification_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the notification manager"""
        if self._running:
            logger.warning("Notification manager already running")
            return

        self._running = True
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        self._worker_task = asyncio.create_task(self._notification_worker())
        logger.info("Notification manager started")

    async def stop(self) -> None:
        """Stop the notification manager"""
        if not self._running:
            return

        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        if self._session:
            await self._session.close()
            self._session = None

        logger.info("Notification manager stopped")

    async def send_event_notification(self, event: AutoHealEvent) -> None:
        """
        Send notification for an auto-heal event

        Args:
            event: The event to send notification for
        """

        logger.info(f"Preparing to send notification for event: {event.event_type}")

        config = config_manager.get_config()

        # Check if notifications are enabled
        if not config.notifications.enabled:
            logger.debug("Notifications disabled, skipping")
            return

        # Check event filters
        if not self._should_notify_for_event(event):
            logger.debug(f"Event type '{event.event_type}' filtered out, skipping notification")
            return

        # Queue the notification
        await self._notification_queue.put(event)
        logger.debug(f"Queued notification for event: {event.event_type}")

    def _should_notify_for_event(self, event: AutoHealEvent) -> bool:
        """
        Check if we should send notification for this event type

        Args:
            event: The event to check

        Returns:
            True if notification should be sent
        """
        config = config_manager.get_config()
        event_filters = config.notifications.event_filters

        # If no filters specified, notify for all events
        if not event_filters:
            return True

        # Check if event type matches any filter
        return event.event_type in event_filters

    async def _notification_worker(self) -> None:
        """Background worker that processes notification queue"""
        while self._running:
            try:
                # Wait for notification with timeout to allow checking _running flag
                try:
                    event = await asyncio.wait_for(
                        self._notification_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process the notification
                await self._process_notification(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notification worker: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_notification(self, event: AutoHealEvent) -> None:
        """
        Process and send notification for an event

        Args:
            event: The event to send notification for
        """
        config = config_manager.get_config()
        notifications_config = config.notifications

        # Prepare notification content
        title, message, priority = self._format_notification(event)

        # Send to all enabled services
        tasks = []

        for service in notifications_config.services:
            if not service.enabled:
                continue

            try:
                if service.type == NotificationType.WEBHOOK:
                    tasks.append(self._send_webhook(service, title, message, event, priority))
                elif service.type == NotificationType.DISCORD:
                    tasks.append(self._send_discord(service, title, message, event, priority))
                elif service.type == NotificationType.SLACK:
                    tasks.append(self._send_slack(service, title, message, event, priority))
                elif service.type == NotificationType.TELEGRAM:
                    tasks.append(self._send_telegram(service, title, message, event, priority))
                elif service.type == NotificationType.NTFY:
                    tasks.append(self._send_ntfy(service, title, message, event, priority))
                elif service.type == NotificationType.GOTIFY:
                    tasks.append(self._send_gotify(service, title, message, event, priority))
                elif service.type == NotificationType.PUSHOVER:
                    tasks.append(self._send_pushover(service, title, message, event, priority))
                else:
                    logger.warning(f"Unsupported notification type: {service.type}")

            except Exception as e:
                logger.error(f"Error preparing notification for {service.type}: {e}")

        # Send all notifications concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Notification failed: {result}")

    def _format_notification(self, event: AutoHealEvent) -> tuple[str, str, NotificationPriority]:
        """
        Format notification content based on event

        Args:
            event: The event to format

        Returns:
            Tuple of (title, message, priority)
        """
        # Determine priority based on event type
        priority = NotificationPriority.NORMAL
        if event.event_type == "quarantine":
            priority = NotificationPriority.HIGH
        elif event.event_type == "unquarantine":
            priority = NotificationPriority.NORMAL
        elif event.event_type == "restart":
            priority = NotificationPriority.NORMAL
        elif event.event_type == "health_check_failed":
            priority = NotificationPriority.HIGH
        elif event.event_type == "auto_monitor":
            priority = NotificationPriority.LOW

        # Format title
        title_map = {
            "restart": "Container Restarted",
            "quarantine": "Container Quarantined",
            "health_check_failed": "Health Check Failed",
            "auto_monitor": "Container Auto-Monitored",
            "unquarantine": "Container Unquarantined",
        }
        title = title_map.get(event.event_type, f" {event.event_type.replace('_', ' ').title()}")

        # Format message
        timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        message = (
            f"**Container:** {event.container_name}\n"
            f"**Event:** {event.event_type}\n"
            f"**Status:** {event.status}\n"
            f"**Restart Count:** {event.restart_count}\n"
            f"**Time:** {timestamp}\n"
            f"**Message:** {event.message}"
        )

        return title, message, priority

    async def _send_webhook(
        self,
        service: Any,
        title: str,
        message: str,
        event: AutoHealEvent,
        priority: NotificationPriority
    ) -> None:
        """Send generic webhook notification"""
        if not service.url:
            logger.warning("Webhook URL not configured")
            return

        payload = {
            "title": title,
            "message": message,
            "priority": priority.value,
            "event": {
                "type": event.event_type,
                "container_id": event.container_id,
                "container_name": event.container_name,
                "status": event.status,
                "restart_count": event.restart_count,
                "timestamp": event.timestamp.isoformat(),
            }
        }

        # Add custom headers if configured
        headers = {"Content-Type": "application/json"}
        if service.headers:
            headers.update(service.headers)

        try:
            async with self._session.post(
                service.url,
                json=payload,
                headers=headers
            ) as response:
                if response.status >= 400:
                    logger.error(f"Webhook failed with status {response.status}: {await response.text()}")
                else:
                    logger.info(f"Webhook notification sent successfully to {service.name}")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

    async def _send_discord(
        self,
        service: Any,
        title: str,
        message: str,
        event: AutoHealEvent,
        priority: NotificationPriority
    ) -> None:
        """Send Discord webhook notification"""
        if not service.url:
            logger.warning("Discord webhook URL not configured")
            return

        # Color based on priority
        color_map = {
            NotificationPriority.LOW: 0x95a5a6,      # Gray
            NotificationPriority.NORMAL: 0x3498db,   # Blue
            NotificationPriority.HIGH: 0xf39c12,     # Orange
            NotificationPriority.CRITICAL: 0xe74c3c  # Red
        }

        embed = {
            "title": title,
            "description": message.replace("**", ""),
            "color": color_map.get(priority, 0x3498db),
            "timestamp": event.timestamp.isoformat(),
            "footer": {
                "text": "Docker Auto-Heal"
            }
        }

        payload = {
            "embeds": [embed],
            "username": service.username or "Docker Auto-Heal"
        }

        try:
            async with self._session.post(service.url, json=payload) as response:
                if response.status >= 400:
                    logger.error(f"Discord webhook failed with status {response.status}")
                else:
                    logger.info(f"Discord notification sent successfully to {service.name}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    async def _send_slack(
        self,
        service: Any,
        title: str,
        message: str,
        event: AutoHealEvent,
        priority: NotificationPriority
    ) -> None:
        """Send Slack webhook notification"""
        if not service.url:
            logger.warning("Slack webhook URL not configured")
            return

        # Format message for Slack
        slack_message = message.replace("**", "*")

        payload = {
            "text": title,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": slack_message
                    }
                }
            ]
        }

        try:
            async with self._session.post(service.url, json=payload) as response:
                if response.status >= 400:
                    logger.error(f"Slack webhook failed with status {response.status}")
                else:
                    logger.info(f"Slack notification sent successfully to {service.name}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def _send_telegram(
        self,
        service: Any,
        title: str,
        message: str,
        event: AutoHealEvent,
        priority: NotificationPriority
    ) -> None:
        """Send Telegram notification"""
        if not service.bot_token or not service.chat_id:
            logger.warning("Telegram bot token or chat ID not configured")
            return

        # Format message for Telegram (Markdown)
        telegram_message = f"*{title}*\n\n{message}"

        url = f"https://api.telegram.org/bot{service.bot_token}/sendMessage"
        payload = {
            "chat_id": service.chat_id,
            "text": telegram_message,
            "parse_mode": "Markdown"
        }

        try:
            async with self._session.post(url, json=payload) as response:
                if response.status >= 400:
                    logger.error(f"Telegram API failed with status {response.status}")
                else:
                    logger.info(f"Telegram notification sent successfully to {service.name}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    async def _send_ntfy(
        self,
        service: Any,
        title: str,
        message: str,
        event: AutoHealEvent,
        priority: NotificationPriority
    ) -> None:
        """Send ntfy.sh notification"""
        if not service.topic:
            logger.warning("Ntfy topic not configured")
            return

        # Ntfy priority mapping (1-5)
        priority_map = {
            NotificationPriority.LOW: "1",
            NotificationPriority.NORMAL: "3",
            NotificationPriority.HIGH: "4",
            NotificationPriority.CRITICAL: "5"
        }

        server_url = service.server_url or "https://ntfy.sh"
        url = f"{server_url}/{service.topic}"

        headers = {
            "Title": title,
            "Priority": priority_map.get(priority, "3"),
            "Tags": "whale,docker"
        }

        # Add authentication if configured
        if service.username and service.password:
            import base64
            credentials = f"{service.username}:{service.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        try:
            async with self._session.post(
                url,
                data=message.replace("**", ""),
                headers=headers
            ) as response:
                if response.status >= 400:
                    logger.error(f"Ntfy failed with status {response.status}")
                else:
                    logger.info(f"Ntfy notification sent successfully to {service.name}")
        except Exception as e:
            logger.error(f"Failed to send Ntfy notification: {e}")

    async def _send_gotify(
        self,
        service: Any,
        title: str,
        message: str,
        event: AutoHealEvent,
        priority: NotificationPriority
    ) -> None:
        """Send Gotify notification"""
        if not service.server_url or not service.app_token:
            logger.warning("Gotify server URL or app token not configured")
            return

        # Gotify priority mapping (0-10)
        priority_map = {
            NotificationPriority.LOW: 2,
            NotificationPriority.NORMAL: 5,
            NotificationPriority.HIGH: 8,
            NotificationPriority.CRITICAL: 10
        }

        url = f"{service.server_url}/message"
        payload = {
            "title": title,
            "message": message.replace("**", ""),
            "priority": priority_map.get(priority, 5)
        }

        headers = {
            "X-Gotify-Key": service.app_token
        }

        try:
            async with self._session.post(url, json=payload, headers=headers) as response:
                if response.status >= 400:
                    logger.error(f"Gotify failed with status {response.status}")
                else:
                    logger.info(f"Gotify notification sent successfully to {service.name}")
        except Exception as e:
            logger.error(f"Failed to send Gotify notification: {e}")

    async def _send_pushover(
        self,
        service: Any,
        title: str,
        message: str,
        event: AutoHealEvent,
        priority: NotificationPriority
    ) -> None:
        """Send Pushover notification"""
        if not service.user_key or not service.api_token:
            logger.warning("Pushover user key or API token not configured")
            return

        # Pushover priority mapping (-2 to 2)
        priority_map = {
            NotificationPriority.LOW: -1,
            NotificationPriority.NORMAL: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.CRITICAL: 2
        }

        url = "https://api.pushover.net/1/messages.json"
        payload = {
            "token": service.api_token,
            "user": service.user_key,
            "title": title,
            "message": message.replace("**", ""),
            "priority": priority_map.get(priority, 0)
        }

        try:
            async with self._session.post(url, data=payload) as response:
                if response.status >= 400:
                    logger.error(f"Pushover failed with status {response.status}")
                else:
                    logger.info(f"Pushover notification sent successfully to {service.name}")
        except Exception as e:
            logger.error(f"Failed to send Pushover notification: {e}")

    async def test_notification(self, service_name: str) -> Dict[str, Any]:
        """
        Send a test notification to verify configuration

        Args:
            service_name: Name of the service to test

        Returns:
            Dict with success status and message
        """
        config = config_manager.get_config()

        # Find the service
        service = None
        for s in config.notifications.services:
            if s.name == service_name:
                service = s
                break

        if not service:
            return {"success": False, "message": f"Service '{service_name}' not found"}

        if not service.enabled:
            return {"success": False, "message": f"Service '{service_name}' is disabled"}

        # Create a test event
        test_event = AutoHealEvent(
            timestamp=datetime.now(timezone.utc),
            container_id="test-container-id",
            container_name="test-container",
            event_type="test",
            restart_count=0,
            status="success",
            message="This is a test notification from Docker Auto-Heal"
        )

        title = "🧪 Test Notification"
        message = "This is a test notification from Docker Auto-Heal. If you received this, your notification service is configured correctly!"
        priority = NotificationPriority.NORMAL

        try:
            if service.type == NotificationType.WEBHOOK:
                await self._send_webhook(service, title, message, test_event, priority)
            elif service.type == NotificationType.DISCORD:
                await self._send_discord(service, title, message, test_event, priority)
            elif service.type == NotificationType.SLACK:
                await self._send_slack(service, title, message, test_event, priority)
            elif service.type == NotificationType.TELEGRAM:
                await self._send_telegram(service, title, message, test_event, priority)
            elif service.type == NotificationType.NTFY:
                await self._send_ntfy(service, title, message, test_event, priority)
            elif service.type == NotificationType.GOTIFY:
                await self._send_gotify(service, title, message, test_event, priority)
            elif service.type == NotificationType.PUSHOVER:
                await self._send_pushover(service, title, message, test_event, priority)
            else:
                return {"success": False, "message": f"Unsupported notification type: {service.type}"}

            return {"success": True, "message": "Test notification sent successfully"}

        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return {"success": False, "message": f"Failed to send test notification: {str(e)}"}


# Global notification manager instance
notification_manager = NotificationManager()
"""
Notification services for Docker Auto-Heal
"""

from app.notifications.notification_manager import NotificationManager

__all__ = ['NotificationManager']

