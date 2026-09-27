"""
Institutional Email Service for PGCB Organization Portal.
Supports bilingual (Bangla / English) transactional email templates with HTML & plain-text formats.
Gracefully handles unconfigured SMTP in local/dev environments.
"""
from __future__ import annotations

import logging
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    success: bool
    recipient: str
    subject: str
    error: str | None = None
    provider: str = "SMTP"


def _wrap_html_template(title: str, content_html: str) -> str:
    """Wraps body content in a responsive, institutional PGCB branded HTML shell."""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f6f8; color: #1f2937; line-height: 1.6; }}
    .container {{ max-width: 600px; margin: 24px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e5e7eb; }}
    .header {{ background: linear-gradient(135deg, #0f3a3a 0%, #006a4e 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }}
    .header p {{ margin: 6px 0 0 0; font-size: 13px; opacity: 0.88; }}
    .body {{ padding: 32px 28px; }}
    .badge {{ display: inline-block; padding: 4px 10px; font-size: 12px; font-weight: 600; border-radius: 4px; background: #e0f2fe; color: #0369a1; margin-bottom: 16px; }}
    .btn {{ display: inline-block; padding: 12px 28px; background-color: #006a4e; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; margin: 20px 0; }}
    .details-box {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; margin: 18px 0; }}
    .details-box table {{ width: 100%; border-collapse: collapse; }}
    .details-box td {{ padding: 6px 0; font-size: 14px; vertical-align: top; }}
    .details-box td.label {{ color: #64748b; font-weight: 500; width: 40%; }}
    .details-box td.value {{ color: #0f172a; font-weight: 600; width: 60%; }}
    .footer {{ background-color: #f9fafb; padding: 20px 24px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #f3f4f6; }}
    .footer a {{ color: #006a4e; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)</h1>
      <p>Power Grid Company of Bangladesh - Employees Welfare &amp; Community Portal</p>
    </div>
    <div class="body">
      {content_html}
    </div>
    <div class="footer">
      <p>&copy; {os.getenv('APP_YEAR', '2026')} Power Grid Bangladesh PLC. All rights reserved.</p>
      <p>This is an automated system notification. Please do not reply directly to this email.</p>
    </div>
  </div>
</body>
</html>"""


class EmailService:
    @staticmethod
    def send_raw_email(to_email: str, subject: str, body_text: str, body_html: str | None = None) -> EmailResult:
        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM", "noreply@pgcb-portal.gov.bd")

        if not host:
            logger.info(f"[DEV EMAIL LOG] To: {to_email} | Subject: {subject}\n{body_text}\n---")
            return EmailResult(success=True, recipient=to_email, subject=subject, provider="MOCK_DEV")

        try:
            msg = EmailMessage()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(body_text)

            if body_html:
                msg.add_alternative(body_html, subtype="html")

            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.starttls()
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)

            logger.info(f"Email sent successfully to {to_email} with subject '{subject}'")
            return EmailResult(success=True, recipient=to_email, subject=subject, provider="SMTP")
        except Exception as exc:
            logger.error(f"Failed to send email to {to_email}: {exc}")
            return EmailResult(success=False, recipient=to_email, subject=subject, error=str(exc)[:500], provider="SMTP")

    @classmethod
    def send_welcome(cls, to_email: str, name: str, membership_id: str) -> EmailResult:
        subject = f"স্বাগতম পিজিসিবি পোর্টালে | Welcome to PGCB Portal ({membership_id})"
        content_html = f"""
        <h2>প্রিয় {name},</h2>
        <p>পিজিসিবি কর্মকর্তা ও কর্মচারী কল্যাণ পোর্টালে আপনাকে স্বাগতম! আপনার সদস্যপদ সফলভাবে সক্রিয় করা হয়েছে।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">সদস্য নম্বর:</td><td class="value">{membership_id}</td></tr>
            <tr><td class="label">ব্যবহারকারীর নাম/ইমেইল:</td><td class="value">{to_email}</td></tr>
            <tr><td class="label">অ্যাক্সেস স্তর:</td><td class="value">সাধারণ সদস্য (General Member)</td></tr>
          </table>
        </div>
        <p>আপনি এখন আপনার ডিজিটাল মেম্বারশিপ কার্ড, সার্কুলার, প্রকাশনা ও কল্যাণমূলক সুবিধাসমূহ দেখতে পারেন।</p>
        <a href="{settings.frontend_url}/portal" class="btn">মেম্বার পোর্টালে লগইন করুন</a>
        """
        body_text = f"প্রিয় {name},\nপিজিসিবি পোর্টালে স্বাগতম। আপনার সদস্য নম্বর: {membership_id}। লগইন করুন: {settings.frontend_url}/portal"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_email_verification(cls, to_email: str, name: str, token: str, verify_url: str) -> EmailResult:
        subject = "আপনার ইমেইল ঠিকানা যাচাই করুন | Verify Your Email"
        content_html = f"""
        <h2>প্রিয় {name},</h2>
        <p>পিজিসিবি পোর্টালে আপনার অ্যাকাউন্ট সুরক্ষা নিশ্চিত করতে নিচের বোতামে ক্লিক করে ইমেইল ঠিকানা যাচাই সম্পন্ন করুন।</p>
        <a href="{verify_url}" class="btn">ইমেইল যাচাই করুন (Verify Email)</a>
        <p style="font-size: 13px; color: #64748b;">এই লিংকটি ২৪ ঘণ্টার জন্য কার্যকর থাকবে। আপনি যদি এই অনুরোধ না করে থাকেন তবে অনুগ্রহ করে এই বার্তাটি উপেক্ষা করুন।</p>
        """
        body_text = f"প্রিয় {name},\nআপনার ইমেইল যাচাই লিংক: {verify_url}\nমেয়াদ: ২৪ ঘণ্টা।"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_password_reset(cls, to_email: str, name: str, token: str, reset_url: str) -> EmailResult:
        subject = "পাসওয়ার্ড রিসেট অনুরোধ | Password Reset Request"
        content_html = f"""
        <h2>প্রিয় {name},</h2>
        <p>আপনার পিজিসিবি অ্যাকাউন্ট পাসওয়ার্ড পরিবর্তনের একটি অনুরোধ গ্রহণ করা হয়েছে। নতুন পাসওয়ার্ড সেট করতে নিচের বোতামে ক্লিক করুন:</p>
        <a href="{reset_url}" class="btn" style="background-color: #0369a1;">পাসওয়ার্ড পরিবর্তন করুন</a>
        <div class="details-box">
          <p style="margin: 0; font-size: 13px; color: #475569;">লিংকটির মেয়াদ ৩০ মিনিট। আপনি যদি এই অনুরোধ না করে থাকেন, দ্রুত সিস্টেম অ্যাডমিনের সাথে যোগাযোগ করুন।</p>
        </div>
        """
        body_text = f"প্রিয় {name},\nপাসওয়ার্ড রিসেট করার লিংক: {reset_url}\nমেয়াদ: ৩০ মিনিট।"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_application_submitted(cls, to_email: str, name: str = '', application_no: str = '', applicant_name: str | None = None) -> EmailResult:
        display_name = applicant_name or name or 'প্রকৌশলী'
        subject = f"সদস্যপদের আবেদন গ্রহণ | Application Received #{application_no}"
        content_html = f"""
        <h2>প্রিয় {display_name},</h2>
        <p>পিজিসিবি মেম্বারশিপের জন্য আপনার অনলাইন আবেদনটি সফলভাবে সিস্টেমে জমা হয়েছে।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">আবেদন ট্র্যাকিং নম্বর:</td><td class="value">{application_no}</td></tr>
            <tr><td class="label">বর্তমান অবস্থা:</td><td class="value">প্রাথমিক যাচাইকরণে অপেক্ষমাণ (Pending Verification)</td></tr>
          </table>
        </div>
        <p>আপনি নিচের লিংক ব্যবহার করে যেকোনো সময় আপনার আবেদনের অগ্রগতি ট্র্যাক করতে পারেন:</p>
        <a href="{settings.frontend_url}/membership/track?app_no={application_no}" class="btn">আবেদন স্ট্যাটাস দেখুন</a>
        """
        body_text = f"প্রিয় {display_name},\nআপনার আবেদন জমা হয়েছে। ট্র্যাকিং নম্বর: {application_no}। স্ট্যাটাস চেক করুন: {settings.frontend_url}/membership/track?app_no={application_no}"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_application_received(cls, to_email: str, applicant_name: str = '', application_no: str = '') -> EmailResult:
        return cls.send_application_submitted(to_email=to_email, name=applicant_name, application_no=application_no)

    @classmethod
    def send_application_approved(cls, to_email: str, name: str = '', membership_id: str = '', portal_url: str | None = None, applicant_name: str | None = None) -> EmailResult:
        display_name = applicant_name or name or 'প্রকৌশলী'
        target_url = portal_url or f"{settings.frontend_url}/portal"
        subject = f"অভিনন্দন! আপনার সদস্যপদ অনুমোদিত হয়েছে | Membership Approved ({membership_id})"
        content_html = f"""
        <h2>অভিনন্দন {display_name}!</h2>
        <p>কর্তৃপক্ষ কর্তৃক আপনার সদস্যপদ আবেদনটি অনুমোদিত হয়েছে। আপনাকে আনুষ্ঠানিকভাবে পিজিসিবি সদস্য হিসেবে অন্তর্ভুক্তি করা হলো।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">সদস্য নম্বর:</td><td class="value">{membership_id}</td></tr>
            <tr><td class="label">অবস্থা:</td><td class="value" style="color: #16a34a;">সক্রিয় (ACTIVE)</td></tr>
          </table>
        </div>
        <p>আপনার প্রোফাইলে লগইন করে ডিজিটাল সদস্য কার্ড ও সার্টিফিকেট ডাউনলোড করুন:</p>
        <a href="{target_url}" class="btn">সদস্য ড্যাশবোর্ডে প্রবেশ করুন</a>
        """
        body_text = f"অভিনন্দন {display_name}! আপনার সদস্যপদ অনুমোদিত হয়েছে। সদস্য আইডি: {membership_id}। পোর্টাল: {target_url}"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_application_rejected(cls, to_email: str, name: str = '', reason: str = '', applicant_name: str | None = None) -> EmailResult:
        display_name = applicant_name or name or 'প্রকৌশলী'
        subject = "সদস্যপদ আবেদন সংক্রান্ত তথ্য | Membership Application Update"
        content_html = f"""
        <h2>প্রিয় {display_name},</h2>
        <p>আপনার সদস্যপদ আবেদনটি পর্যালোচনার পর এই মুহূর্তে গ্রহণ করা সম্ভব হয়নি।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">পর্যালোচনা মন্তব্য/কারণ:</td><td class="value">{reason}</td></tr>
          </table>
        </div>
        <p>প্রয়োজনীয় কাগজপত্র বা তথ্য সংশোধন করে আপনি পুনরায় আবেদন করতে পারেন। প্রয়োজনে হেল্পডেস্কে যোগাযোগ করুন।</p>
        """
        body_text = f"প্রিয় {display_name},\nআপনার আবেদন পর্যালোচনা শেষে স্থগিত/বাতিল করা হয়েছে। কারণ: {reason}।"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_payment_received(cls, to_email: str, name: str, amount: float, trx_id: str, purpose: str) -> EmailResult:
        subject = f"পেমেন্ট প্রাপ্তি রসিদ | Payment Receipt #{trx_id}"
        content_html = f"""
        <h2>ধন্যবাদ {name},</h2>
        <p>আপনার পেমেন্ট সফলভাবে গ্রহণ করা হয়েছে এবং অ্যাকাউন্টে জমা করা হয়েছে।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">লেনদেন আইডি (TrxID):</td><td class="value">{trx_id}</td></tr>
            <tr><td class="label">বিবরণ / উদ্দেশ্য:</td><td class="value">{purpose}</td></tr>
            <tr><td class="label">জমাকৃত পরিমাণ:</td><td class="value">৳ {amount:,.2f} BDT</td></tr>
          </table>
        </div>
        <p>আপনার প্রোফাইল থেকে অর্থপ্রদানের অফিসিয়াল রসিদ প্রিন্ট করতে পারেন।</p>
        """
        body_text = f"ধন্যবাদ {name},\nপেমেন্ট প্রাপ্তি নিশ্চিত করা হলো। TrxID: {trx_id}, পরিমাণ: ৳ {amount:,.2f}, বিবরণ: {purpose}।"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_payment_receipt(cls, to_email: str, payer_name: str, amount: Any, transaction_id: str, purpose: str) -> EmailResult:
        subject = f"পেমেন্ট প্রাপ্তি রসিদ | Payment Receipt #{transaction_id}"
        body_text = f"ধন্যবাদ {payer_name},\nপেমেন্ট প্রাপ্তি নিশ্চিত করা হলো। TrxID: {transaction_id}, পরিমাণ: {amount}, বিবরণ: {purpose}।"
        content_html = f"""
        <h2>ধন্যবাদ {payer_name},</h2>
        <p>আপনার পেমেন্ট সফলভাবে গ্রহণ করা হয়েছে।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">লেনদেন আইডি (TrxID):</td><td class="value">{transaction_id}</td></tr>
            <tr><td class="label">বিবরণ / উদ্দেশ্য:</td><td class="value">{purpose}</td></tr>
            <tr><td class="label">জমাকৃত পরিমাণ:</td><td class="value">{amount}</td></tr>
          </table>
        </div>
        """
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_certificate_issued(cls, to_email: str, recipient_name: str, certificate_type: str, certificate_number: str, verification_url: str) -> EmailResult:
        subject = f"নতুন সনদপত্র ইস্যু করা হয়েছে | Certificate Issued ({certificate_number})"
        body_text = f"প্রিয় {recipient_name},\nআপনার {certificate_type} সনদপত্র ({certificate_number}) ইস্যু করা হয়েছে। যাচাইকরণ লিংক: {verification_url}"
        content_html = f"""
        <h2>প্রিয় {recipient_name},</h2>
        <p>আপনার প্রাতিষ্ঠানিক সনদপত্র সফলভাবে ইস্যু করা হয়েছে।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">সনদপত্র নম্বর:</td><td class="value">{certificate_number}</td></tr>
            <tr><td class="label">ধরন:</td><td class="value">{certificate_type}</td></tr>
          </table>
        </div>
        <a href="{verification_url}" class="btn">সনদ যাচাই করুন</a>
        """
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_renewal_notice(cls, to_email: str, name: str, expiry_date: str, renew_url: str) -> EmailResult:
        subject = "সদস্যপদ নবায়ন নোটিশ | PGCB Membership Renewal Notice"
        content_html = f"""
        <h2>প্রিয় {name},</h2>
        <p>আপনার পিজিসিবি সদস্যপদের মেয়াদ আগামী <strong>{expiry_date}</strong> তারিখে শেষ হতে যাচ্ছে। নিরবচ্ছিন্ন সুযোগ-সুবিধা ও সার্ভিস বজায় রাখতে অনুগ্রহ করে নির্ধারিত সময়ের পূর্বে সদস্যপদ নবায়ন সম্পন্ন করুন।</p>
        <a href="{renew_url}" class="btn">অনলাইনে সদস্যপদ নবায়ন করুন</a>
        """
        body_text = f"প্রিয় {name},\nআপনার সদস্যপদের মেয়াদ শেষ হবে: {expiry_date}। নবায়ন করতে ভিজিট করুন: {renew_url}"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_event_registered(cls, to_email: str, name: str, event_title: str, event_date: str, venue: str) -> EmailResult:
        subject = f"ইভেন্ট নিবন্ধন নিশ্চিতকরণ | Event Registration: {event_title}"
        content_html = f"""
        <h2>প্রিয় {name},</h2>
        <p><strong>{event_title}</strong> অনুষ্ঠানে আপনার অংশগ্রহণ নিবন্ধন নিশ্চিত করা হয়েছে।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">তারিখ ও সময়:</td><td class="value">{event_date}</td></tr>
            <tr><td class="label">স্থান/ভেন্যু:</td><td class="value">{venue}</td></tr>
          </table>
        </div>
        <p>অনুষ্ঠানে প্রবেশের জন্য আপনার মেম্বারশিপ কার্ড অথবা ডিজিটাল টিকিট প্রদর্শন করুন।</p>
        """
        body_text = f"প্রিয় {name},\n{event_title} ইভেন্টে আপনার নিবন্ধন নিশ্চিত করা হয়েছে। সময়: {event_date}। স্থান: {venue}।"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

    @classmethod
    def send_event_confirmation(cls, to_email: str, participant_name: str, event_title: str, ticket_code: str, event_date: str, location: str) -> EmailResult:
        return cls.send_event_registered(to_email=to_email, name=participant_name, event_title=f"{event_title} ({ticket_code})", event_date=event_date, venue=location)

    @classmethod
    def send_security_alert(cls, to_email: str, name: str, action_desc: str, time_str: str, ip_addr: str) -> EmailResult:
        subject = "নিরাপত্তা সতর্কতা | Security Alert: Account Activity"
        content_html = f"""
        <h2>প্রিয় {name},</h2>
        <p style="color: #dc2626; font-weight: 600;">আপনার পিজিসিবি অ্যাকাউন্টে একটি গুরুত্বপূর্ণ নিরাপত্তা পরিবর্তন শনাক্ত করা হয়েছে।</p>
        <div class="details-box">
          <table>
            <tr><td class="label">কার্যক্রম:</td><td class="value">{action_desc}</td></tr>
            <tr><td class="label">সময়:</td><td class="value">{time_str}</td></tr>
            <tr><td class="label">আইপি ঠিকানা:</td><td class="value">{ip_addr}</td></tr>
          </table>
        </div>
        <p>আপনি যদি এই পরিবর্তন নিজে না করে থাকেন, তবে অবিলম্বে আপনার পাসওয়ার্ড পরিবর্তন করুন এবং আইটি অ্যাডমিনের সাথে যোগাযোগ করুন।</p>
        """
        body_text = f"নিরাপত্তা সতর্কতা: প্রিয় {name},\nআপনার অ্যাকাউন্টে {action_desc} সম্পন্ন হয়েছে। সময়: {time_str}, IP: {ip_addr}।"
        return cls.send_raw_email(to_email, subject, body_text, _wrap_html_template(subject, content_html))

