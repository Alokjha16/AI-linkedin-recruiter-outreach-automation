"""
config.py - Configuration Management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
RESUME_DIR = BASE_DIR / "resumes"
CREDENTIALS_DIR = BASE_DIR / "credentials"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

OUTPUT_DIR.mkdir(exist_ok=True)
RESUME_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)

LEADS_CSV = OUTPUT_DIR / "leads.csv"
SENT_LOG_CSV = OUTPUT_DIR / "sent_log.csv"
CANDIDATE_DATA_FILE = BASE_DIR / "candidate_data.json"

GMAIL_CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
GMAIL_TOKEN_FILE = CREDENTIALS_DIR / "token.json"
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "rahuljha1229@gmail.com")
SENDER_NAME = os.getenv("SENDER_NAME", "Alok Jha")

TRACKING_EMAIL = "Quinn@jpitstaffing.com"
CLIENT_CC_EMAIL = "santoshanoushikakomala@gmail.com"

CURRENT_CANDIDATE = {
    "full_name": "Santosh Anoushika Komala",
    "name": "Santosh Anoushika Komala",
    "email": "santoshanoushikakomala@gmail.com",
    "phone": "+1 203 809 9717",
    "linkedin": "https://www.linkedin.com/in/anoushika-komala/",
    "experience": "2 years",
    "total_experience": "2 years",
    "availability": "M-F: 11 AM - 6 PM EST",
    "location": "West Haven, CT 06516",
    "current_location": "West Haven, CT 06516",
    "work_authorization": "F1 OPT",
    "preferred_location": "Open to Relocate",
    "open_to_relocate": "Yes",
    "employer_email": "Quinn@jpitstaffing.com",
    "employer_phone": "+1 5716265445",
}

LINKEDIN_BASE_URL = "https://www.linkedin.com"
LINKEDIN_SEARCH_URL = "https://www.linkedin.com/search/results/content/"

DEFAULT_SEARCH_KEYWORDS = [
    "Cybersecurity Analyst hiring",
    "SOC Analyst hiring",
    "Security Analyst hiring",
    "Information Security Analyst hiring",
    "Cyber Security Analyst hiring",
    "Cybersecurity Engineer hiring",
    "SOC Analyst Level 1 hiring",
    "SOC Analyst L1 hiring",
    "Entry Level SOC Analyst hiring",
    "Junior Cybersecurity Analyst hiring",
    "Threat Intelligence Analyst hiring",
    "Incident Response Analyst hiring",
    "SIEM Analyst hiring",
    "Splunk Analyst hiring",
    "Security Operations Center Analyst hiring",
    "IAM Analyst hiring",
    "Identity Access Management Analyst hiring",
    "Active Directory Analyst hiring",
    "Vulnerability Analyst hiring",
    "Vulnerability Management Analyst hiring",
    "GRC Analyst hiring",
    "IT Security Analyst hiring",
    "Cloud Security Analyst hiring",
    "Cyber Defense Analyst hiring",
    "Security Monitoring Analyst hiring",
]

BAD_LEAD_KEYWORDS = [
    "bench sales",
    "bench-sales",
    "hotlist",
    "hot list",
    "consultant available",
    "available consultant",
    "vendor list",
    "marketing bench",
    "on bench",
    "bench candidate",
    "c2c candidates available",
    "candidate available",
    "available candidates",
    "requirements & hotlist",
    "requirements and hotlist",
    "looking for c2c candidates",
    "share hotlist",
    "hotlist sharing",
    "available consultants",
    "bench recruiter",
    "bench marketing",
    "training and placement",
    "placement support",
    "job support",
    "proxy interview",
    "fake profile",
    "pay after placement",
]

GOOD_LEAD_KEYWORDS = [
    "hiring",
    "need",
    "requirement",
    "requirements",
    "immediate",
    "looking for",
    "opening",
    "role",
    "position",
    "opportunity",
    "share resume",
    "send resume",
    "email resume",
    "interested candidates",
    "remote",
    "hybrid",
    "onsite",
    "contract",
    "full time",
    "part time",
    "cybersecurity",
    "cyber security",
    "security analyst",
    "soc analyst",
    "soc",
    "siem",
    "splunk",
    "incident response",
    "threat intelligence",
    "threat hunting",
    "vulnerability",
    "vulnerability management",
    "iam",
    "identity access management",
    "active directory",
    "security operations",
    "information security",
    "cloud security",
    "grc",
    "nist",
    "mitre",
    "osint",
    "network security",
]

MIN_ACTION_DELAY = 0.1
MAX_ACTION_DELAY = 0.25

MAX_POSTS_PER_KEYWORD = 50
MAX_SCROLL_ATTEMPTS = 4
PAGE_LOAD_TIMEOUT = 20

EMAIL_SEND_DELAY = 7
MAX_EMAILS_PER_SESSION = 100

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

DEFAULT_RESUME_FILENAME = os.getenv(
    "DEFAULT_RESUME_FILENAME",
    "Santosh_Anoushika_Komala_Resume.pdf"
)

DEFAULT_RESUME_PATH = RESUME_DIR / DEFAULT_RESUME_FILENAME

CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR", "")
HEADLESS_MODE = False