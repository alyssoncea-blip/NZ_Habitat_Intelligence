"""Notification blocks for Prefect flow alerts."""
import os
import logging

from prefect.blocks.notifications import SlackWebhook

logger = logging.getLogger(__name__)


def setup_notification_blocks():
    """Create notification blocks if environment variables are set."""
    blocks_created = []

    slack_url = os.getenv("ALERT_WEBHOOK_URL")
    if slack_url:
        try:
            slack_block = SlackWebhook(url=slack_url)
            slack_block.save("nz-habitat-slack-alerts", overwrite=True)
            blocks_created.append("nz-habitat-slack-alerts")
            logger.info("Slack notification block created")
        except Exception as e:
            logger.warning("Failed to create Slack block: %s", e)

    email_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS")
    if email_recipients:
        try:
            from prefect.blocks.notifications import EmailSenderBlock
            email_block = EmailSenderBlock(
                smtp_type="smtp",
                smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                smtp_user=os.getenv("SMTP_USER", ""),
            )
            email_block.save("nz-habitat-email-alerts", overwrite=True)
            blocks_created.append("nz-habitat-email-alerts")
            logger.info("Email notification block created")
        except Exception as e:
            logger.warning("Failed to create Email block: %s", e)

    return blocks_created


if __name__ == "__main__":
    blocks = setup_notification_blocks()
    if blocks:
        print(f"Created notification blocks: {', '.join(blocks)}")
    else:
        print("No notification blocks created (set ALERT_WEBHOOK_URL or ALERT_EMAIL_RECIPIENTS)")
