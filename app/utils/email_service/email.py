import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class EmailService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str = None,
        from_email: str = None,
    ):
        """
        Generic email sender for any purpose.
        """
        from_email = settings.SMTP.SMTP_FROM
        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] =to_email
        msg["Subject"] = subject

        if plain_content:
            msg.attach(MIMEText(plain_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP.SMTP_HOST,
                port=settings.SMTP.SMTP_PORT,
                start_tls=True,
                username=settings.SMTP.SMTP_USER,
                password=settings.SMTP.SMTP_PASS,
            )
            logger.info(f"✅ Email sent to {to_email}: {subject}")
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")



class UserEmailTemplate:
    """Handles user-related emails (welcome, account created, etc.)"""

    @staticmethod
    async def send_account_created_email(user_email: str, full_name: str):
        subject = "🎉 Welcome to GoldVault!"
        html = f"""
        <p>Hi <b>{full_name}</b>,</p>
        <p>Your GoldVault account has been successfully created by our admin team.</p>
        <p>You can now log in to start investing, buying, and managing gold securely.</p>
        <br>
        <p>— The GoldVault Team</p>
        """
        plain = f"""
        Hi {full_name},

        Your GoldVault account has been successfully created by our admin team.
        You can now log in to start investing, buying, and managing gold securely.

        — The GoldVault Team
        """

        try:
            await EmailService.send_email(
                to_email=user_email,
                subject=subject,
                html_content=html,
                plain_content=plain,
            )
            logger.info(f"✅ Sent account creation email to {user_email}")
        except Exception as e:
            logger.error(f"❌ Failed to send account creation email: {e}")

class SubscriptionEmailTemplate:
    """Handles all subscription-related emails."""

    @staticmethod
    async def send_subscription_created_email(user_email: str, full_name: str, plan: dict):
        subject = f"📈 Your GoldVault Plan Subscription is Active!"

        plan_name = plan.get("plan_name", "N/A")
        minimum_investment_amount = plan.get("minimum_investment_amount", "N/A")
        
        html = f"""
        <p>Hi <b>{full_name}</b>,</p>
        <p>Congratulations! You have successfully subscribed to the <b>{plan_name}</b> plan.</p>
        <p>Here are your plan details:</p>
        <ul>
            <li><b>Plan Name:</b> {plan_name}</li>
            <li><b>Minimum Investment Amount:</b> ₹{minimum_investment_amount}</li>

        </ul>
        <p>Your investment journey has just begun. Stay tuned for updates and gold growth insights!</p>
        <br>
        <p>— The GoldVault Team</p>
        """

        plain = f"""
        Hi {full_name},

        Congratulations! You have successfully subscribed to the '{plan_name}' plan.

        Plan Details:
        - Plan Name: {plan_name}
        - Minimum Investment Amount: ₹{minimum_investment_amount}


        Your investment journey has just begun. Stay tuned for updates!

        — The GoldVault Team
        """

        try:
            await EmailService.send_email(
                to_email=user_email,
                subject=subject,
                html_content=html,
                plain_content=plain,
            )
            logger.info(f"✅ Sent subscription created email to {user_email}")
        except Exception as e:
            logger.error(f"❌ Failed to send subscription created email: {e}")

class InvestmentConfirmationTemplate:
    @staticmethod
    async def send_investment_confirmation(
        to_email: str,
        user_name: str,
        plan_name: str,
        payment_amount: float,
        grams_purchased: float,
        deposit_date: str,
        currency: str,
        total_invested: float,
        total_grams: float,
    ):
        subject = f"Investment Confirmation - {plan_name}"
        body = f"""
        Hi {user_name},

        Your investment for the plan <b>{plan_name}</b> has been successfully recorded.

        <b>Transaction Details:</b><br>
        Date: {deposit_date}<br>
        Amount: {payment_amount} {currency}<br>
        Gold Purchased: {grams_purchased} grams<br>

        <b>Your Updated Portfolio:</b><br>
        Total Invested: {total_invested} {currency}<br>
        Total Gold Holdings: {total_grams} grams<br>

        Thank you for investing with us!
        """
        await EmailService.send_email(to_email, subject, body)
