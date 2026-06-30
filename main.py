#!/usr/bin/env python3

import argparse
import logging
import random.
import re
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("automation.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

from config import (
    DRY_RUN,
    DEFAULT_SEARCH_KEYWORDS,
    DEFAULT_RESUME_PATH,
    EMAIL_SEND_DELAY,
    MAX_EMAILS_PER_SESSION,
    LEADS_CSV,
    CURRENT_CANDIDATE,
    SENDER_EMAIL,
    SENDER_NAME,
)

try:
    from config import TRACKING_EMAIL
except Exception:
    TRACKING_EMAIL = "Quinn@jpitstaffing.com"

from src.linkedin_scraper import scrape_linkedin_posts
from src.gmail_service import authenticate_gmail, send_or_draft
from src.csv_manager import save_leads, get_unsent_leads, log_sent_email, preview_leads
from src.email_template import load_candidate_data, generate_subject, generate_email_body, generate_email_html_body
from src.resume_customizer import customize_resume


MISSING_VALUES = ["", "0", "none", "nan", "n/a", "null", "not available", "not avail", "not mentioned"]


def clean_value(value, default=""):
    if value is None:
        return default
    value = str(value).strip()
    if value.lower() in MISSING_VALUES:
        return default
    return value


def get_value(data, keys, default=""):
    for key in keys:
        try:
            value = clean_value(data.get(key, ""))
            if value:
                return value
        except Exception:
            pass
    return default


def load_current_candidate():
    try:
        candidate = load_candidate_data()
        if candidate:
            return candidate
    except Exception as e:
        print(f"\n⚠️ Could not load candidate_data.json: {e}")

    print("\nℹ️ Using CURRENT_CANDIDATE from config.py")
    return CURRENT_CANDIDATE


def get_post_text_from_lead(lead):
    cols = [
        "full_post_text",
        "post_text",
        "post_content",
        "content",
        "post_snippet",
        "description",
        "job_description",
        "text",
    ]

    for col in cols:
        value = get_value(lead, [col], "")
        if value:
            return value

    return " ".join([
        get_value(lead, ["job_role", "job_title", "role"], ""),
        get_value(lead, ["location"], ""),
        get_value(lead, ["emails"], ""),
    ]).strip()


def normalize_role_category(job_role, post_text=""):
    text = f"{job_role} {post_text}".lower()

    if any(x in text for x in ["soc analyst", "security operations center", "soc l1", "soc level 1", "alert triage"]):
        return "soc_analyst"

    if any(x in text for x in ["iam", "identity access", "identity & access", "active directory", "rbac", "access provisioning"]):
        return "iam_analyst"

    if any(x in text for x in ["siem", "splunk", "sentinel", "qradar", "security monitoring"]):
        return "siem_security_analyst"

    if any(x in text for x in ["incident response", "incident responder", "security incident"]):
        return "incident_response"

    if any(x in text for x in ["threat intelligence", "threat hunting", "osint", "ioc"]):
        return "threat_intelligence"

    if any(x in text for x in ["vulnerability", "vulnerability management", "security assessment", "nessus", "qualys"]):
        return "vulnerability_management"

    if any(x in text for x in ["cloud security", "aws security", "azure security", "gcp security"]):
        return "cloud_security"

    if any(x in text for x in ["grc", "risk compliance", "security compliance", "nist", "audit"]):
        return "grc_analyst"

    if any(x in text for x in ["cybersecurity", "cyber security", "security analyst", "information security", "it security"]):
        return "cybersecurity_analyst"

    safe = re.sub(r"[^a-z0-9]+", "_", text[:50]).strip("_")
    return safe or "cybersecurity_general"


def score_lead(lead):
    text = " ".join([
        get_value(lead, ["full_post_text"], ""),
        get_value(lead, ["post_snippet"], ""),
        get_value(lead, ["job_role", "job_title", "role", "keyword"], ""),
        get_value(lead, ["location"], ""),
        get_value(lead, ["emails"], ""),
    ]).lower()

    score = 0

    good_words = [
        "hiring", "urgent", "immediate", "send resume", "share resume",
        "email", "looking for", "requirement", "remote", "contract",
        "opening", "available role", "submit profile", "resume"
    ]

    cyber_role_words = [
        "cybersecurity", "cyber security", "security analyst", "information security",
        "it security", "soc analyst", "soc", "security operations center",
        "siem", "splunk", "sentinel", "incident response", "incident responder",
        "threat intelligence", "threat hunting", "osint", "ioc",
        "vulnerability", "vulnerability management", "iam", "identity access",
        "active directory", "rbac", "grc", "nist", "mitre", "cloud security",
        "network security", "endpoint security"
    ]

    bad_words = [
        "bench sales", "hotlist", "hot list", "w2 only", "no c2c",
        "training", "course", "available candidates", "available consultants",
        "marketing support", "placement support", "we provide consultants",
        "h1b transfer", "fake profile", "proxy interview"
    ]

    for word in good_words:
        if word in text:
            score += 2

    for word in cyber_role_words:
        if word in text:
            score += 4

    for word in bad_words:
        if word in text:
            score -= 15

    if "@" in text:
        score += 5

    if any(x in text for x in ["united states", "usa", "remote", "connecticut", "ct", "new york", "ny", "new jersey", "nj", "us"]):
        score += 2

    return score


def filter_and_rank_leads(unsent_leads, min_score=8):
    if unsent_leads.empty:
        return unsent_leads

    leads = unsent_leads.copy()
    leads["lead_score"] = leads.apply(score_lead, axis=1)
    leads = leads[leads["lead_score"] >= min_score]
    leads = leads.sort_values("lead_score", ascending=False)

    return leads


def send_or_draft_safe(**kwargs):
    try:
        return send_or_draft(**kwargs, bcc=TRACKING_EMAIL)
    except TypeError:
        return send_or_draft(**kwargs)


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      🔗 LinkedIn Job Post Email Automation                   ║
║      📧 Gmail API + Resume Customization                    ║
║      ⚡ Speed + Lead Scoring Optimized                      ║
║                                                              ║
║      Author: Alok Jha                                        ║
║      Version: 1.9.0 Siddhu Scale Optimized                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def parse_arguments():
    parser = argparse.ArgumentParser(description="LinkedIn Recruiter Email Automation")
    parser.add_argument("--send", action="store_true", default=False)
    parser.add_argument("--skip-scrape", action="store_true", default=False)
    parser.add_argument("--keywords", nargs="+", default=None)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--max-emails", type=int, default=MAX_EMAILS_PER_SESSION)
    parser.add_argument("--min-score", type=int, default=8)
    return parser.parse_args()


def step_scrape(keywords):
    print("\n" + "=" * 60)
    print("  STEP 1: SCRAPING LINKEDIN POSTS")
    print("=" * 60)

    print(f"\nKeywords to search: {keywords}")
    leads = scrape_linkedin_posts(keywords=keywords)

    if leads:
        save_leads(leads)
        print(f"\n✅ Scraping complete! Found {len(leads)} leads with email addresses.")
    else:
        print("\n⚠️ No leads with email addresses found.")

    return leads


def step_preview_and_confirm(min_score):
    print("\n" + "=" * 60)
    print("  STEP 2: PREVIEW + LEAD SCORING")
    print("=" * 60)

    unsent_leads = get_unsent_leads()

    if unsent_leads.empty:
        print("\n📭 No unsent leads found.")
        return None

    ranked_leads = filter_and_rank_leads(unsent_leads, min_score=min_score)

    if ranked_leads.empty:
        print(f"\n📭 No high-quality leads found after scoring. Min score: {min_score}")
        return None

    print(f"\n✅ Qualified leads after scoring: {len(ranked_leads)}")
    preview_leads(ranked_leads)

    print("\n✅ Auto mode enabled. Proceeding to Email...")
    return ranked_leads


def step_send_emails(unsent_leads, dry_run, fallback_resume_path, max_emails):
    mode_label = "DRAFTING" if dry_run else "SENDING"
    print("\n" + "=" * 60)
    print(f"  STEP 3: {mode_label} EMAILS")
    print("=" * 60)

    candidate = load_current_candidate()

    client_email = get_value(candidate, ["email"], "siddhukolamala24@gmail.com")
    candidate_name = get_value(candidate, ["name", "full_name"], "Siddhu Kolamala")

    print("\n👤 Current Candidate:")
    print(f"   Name: {candidate_name}")
    print(f"   Email: {client_email}")
    print(f"   Phone: {get_value(candidate, ['phone', 'mobile'], '+1 973-687-9494')}")
    print(f"   Availability: {get_value(candidate, ['availability'], 'Immediate')}")

    print("\n📧 Email Routing:")
    print("   From: Gmail authenticated sender")
    print("   To: Recruiter")
    print(f"   Cc: {client_email}")
    print(f"   Bcc: {TRACKING_EMAIL}")

    print("\n🔐 Authenticating Gmail API...")

    try:
        gmail_service = authenticate_gmail()
    except Exception as e:
        print(f"\n❌ Gmail authentication failed: {e}")
        return

    resume_cache = {}

    sent_count = 0
    failed_count = 0

    for lead_index, (_, lead) in enumerate(unsent_leads.iterrows(), start=1):
        if sent_count >= max_emails:
            print(f"\n⚠️ Reached maximum emails per session ({max_emails}).")
            break

        emails = [e.strip() for e in str(lead.get("emails", "")).split(",") if e.strip()]
        if not emails:
            continue

        recruiter_name = get_value(lead, ["recruiter_name", "name", "contact_name"], "Recruiter")
        job_role = get_value(lead, ["job_role", "job_title", "role", "keyword"], "Marketing Role")
        post_text = get_post_text_from_lead(lead)
        role_category = normalize_role_category(job_role, post_text)

        if role_category in resume_cache:
            attach_path = resume_cache[role_category]
            print(f"\n♻️ Reusing cached resume for role category: {role_category}")
        else:
            try:
                custom_resume_path = Path(customize_resume(post_text, lead_index))
                attach_path = custom_resume_path
                resume_cache[role_category] = attach_path
                print(f"\n📄 Custom resume created for {role_category}: {attach_path}")
            except Exception as e:
                print(f"\n⚠️ Custom resume failed for lead {lead_index}: {e}")
                attach_path = fallback_resume_path if fallback_resume_path.exists() else None

        for email_addr in emails:
            if sent_count >= max_emails:
                break

            if email_addr.lower() == SENDER_EMAIL.lower():
                print(f"\n  ⚠️ Skipping self-email: {email_addr}")
                continue

            if email_addr.lower() == client_email.lower():
                print(f"\n  ⚠️ Skipping client email as recruiter: {email_addr}")
                continue

            subject = generate_subject(lead, candidate)
            body_text = generate_email_body(lead, candidate)
            body_html = generate_email_html_body(lead, candidate)

            print(f"\n  [{sent_count + 1}] {'Drafting' if dry_run else 'Sending'} to: {email_addr}")
            print(f"      Score: {score_lead(lead)}")
            print(f"      Recruiter: {recruiter_name}")
            print(f"      Role: {job_role}")
            print(f"      Resume Category: {role_category}")
            print(f"      Subject: {subject}")

            try:
                result = send_or_draft_safe(
                    service=gmail_service,
                    to=email_addr,
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    attachment_path=attach_path,
                    dry_run=dry_run,
                    cc=client_email,
                )
            except Exception as e:
                result = {"status": "failed", "message_id": "", "error": str(e)}

            status = result.get("status", "failed")
            message_id = result.get("message_id", "")

            log_sent_email(
                recipient_email=email_addr,
                recruiter_name=recruiter_name,
                job_role=job_role,
                subject=subject,
                status=status,
                message_id=message_id,
            )

            if status in ("sent", "drafted"):
                print(f"      ✅ {status.upper()} — ID: {message_id}")
                sent_count += 1
            else:
                print(f"      ❌ FAILED — {result.get('error', 'Unknown error')}")
                failed_count += 1

            if sent_count < max_emails:
                time.sleep(EMAIL_SEND_DELAY + random.uniform(1, 4))

    print("\n" + "=" * 60)
    print("  EMAIL SUMMARY")
    print("=" * 60)
    print(f"  ✅ Successfully {'drafted' if dry_run else 'sent'}: {sent_count}")
    print(f"  ❌ Failed: {failed_count}")
    print("  📄 Sent log: outputs/sent_log.csv")
    print("  📁 Custom resumes: outputs/resumes/")
    print("=" * 60)


def main():
    print_banner()
    args = parse_arguments()

    dry_run = DRY_RUN and not args.send
    keywords = args.keywords or DEFAULT_SEARCH_KEYWORDS
    fallback_resume_path = Path(args.resume) if args.resume else DEFAULT_RESUME_PATH

    print(f"  Mode: {'DRY-RUN' if dry_run else 'LIVE SEND'}")
    print(f"  Fallback Resume: {fallback_resume_path}")
    print(f"  Max emails: {args.max_emails}")
    print(f"  Min lead score: {args.min_score}")

    if not args.skip_scrape:
        step_scrape(keywords)
    else:
        print("\n⏭️ Skipping LinkedIn scrape. Using existing leads.csv.")
        if not LEADS_CSV.exists():
            print("\n❌ Error: leads.csv not found! Run without --skip-scrape first.")
            sys.exit(1)

    unsent_leads = step_preview_and_confirm(args.min_score)

    if unsent_leads is None:
        print("\n👋 Exiting. No emails to process.")
        return

    step_send_emails(unsent_leads, dry_run, fallback_resume_path, args.max_emails)

    print("\n🎉 Automation complete!\n")


if __name__ == "__main__":
    main()
