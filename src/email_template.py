import json
import random
import re
from html import escape
from pathlib import Path


MISSING_VALUES = [
    "",
    "0",
    "none",
    "nan",
    "n/a",
    "null",
    "not available",
    "not avail",
    "not mentioned",
]


def load_candidate_data(path="candidate_data.json"):
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{path} not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_value(value, default=""):
    if value is None:
        return default

    value = str(value).strip()

    if value.lower() in MISSING_VALUES:
        return default

    return value


def is_valid_value(value):
    return bool(clean_value(value, ""))


def get_value(data, keys, default=""):
    if data is None:
        data = {}

    for key in keys:
        try:
            value = clean_value(data.get(key, ""))
            if value:
                return value
        except Exception:
            pass

    return default


def clean_requirement_details(text):
    text = clean_value(text, "")

    if not text:
        return ""

    text = text.replace("\r", "\n").replace("\t", " ")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = []

    junk_patterns = [
        r"^\d+\s+reaction[s]?$",
        r"^\d+\s+comment[s]?$",
        r"^\d+\s+repost[s]?$",
        r"^\d+\s+share[s]?$",
        r"^\d+\s+like[s]?$",
        r"^like$",
        r"^comment$",
        r"^share$",
        r"^repost$",
        r"^send$",
        r"^follow$",
        r"^connect$",
        r"^message$",
        r"^see more$",
        r"^show more$",
        r"^not available$",
        r"^not avail$",
        r"^not mentioned$",
        r"^…\s*more$",
        r"^\.\.\.\s*more$",
    ]

    for line in lines:
        low = line.lower().strip()

        if low in MISSING_VALUES:
            continue

        if any(re.match(pattern, low) for pattern in junk_patterns):
            continue

        cleaned.append(line)

    result = "\n".join(cleaned).strip()

    if len(result) > 1800:
        result = result[:1800].rsplit("\n", 1)[0].strip()

    return result


def clean_post_url(post_url):
    post_url = clean_value(post_url, "")

    if not post_url:
        return ""

    if not post_url.startswith("http"):
        return ""

    bad_values = [
        "https://linkedin.com",
        "https://www.linkedin.com",
        "http://linkedin.com",
        "http://www.linkedin.com",
    ]

    if post_url.rstrip("/") in [x.rstrip("/") for x in bad_values]:
        return ""

    return post_url


def remove_bad_lines(body):
    if not body:
        return ""

    lines = [line.rstrip() for line in body.splitlines()]
    cleaned = []

    for line in lines:
        low = line.strip().lower()

        if low in MISSING_VALUES:
            continue

        cleaned.append(line)

    body = "\n".join(cleaned).strip()
    body = re.sub(r"\n{4,}", "\n\n\n", body)

    return body.strip()


def get_recruiter_greeting(recruiter_name):
    name = clean_value(recruiter_name)

    bad_names = {
        "linkedin recruiter",
        "recruiter",
        "hiring manager",
        "unknown",
    }

    if name.lower() in bad_names:
        return "Hi,"

    return f"Hi {name}," if name else "Hi,"


def shorten_role(role):
    role = clean_value(role, "Marketing Role")

    replacements = {
        "Hiring ": "",
        "Need ": "",
        "Looking for ": "",
        "Immediate ": "",
        "Requirement": "",
        "requirements": "",
        "email": "",
    }

    for old, new in replacements.items():
        role = role.replace(old, new)

    role = re.sub(r"\s+", " ", role).strip()
    return role[:60] if role else "Marketing Role"


def generate_subject(lead, candidate):
    job_title = shorten_role(
        get_value(lead, ["job_title", "job_role", "role", "keyword"], "Marketing Role")
    )

    candidate_name = get_value(candidate, ["full_name", "name"], "Siddhu Kolamala")
    availability = get_value(candidate, ["availability"], "Immediate")
    location = get_value(candidate, ["current_location", "location"], "New York, NY")

    subjects = [
        f"{candidate_name} | {job_title} | {availability}",
        f"Available {job_title} Candidate – {candidate_name}",
        f"{job_title} Profile for Review – {candidate_name}",
        f"{candidate_name} for {job_title} Requirement",
        f"Immediate {job_title} Candidate – {candidate_name}",
        f"{job_title} Resume – {candidate_name} | {location}",
        f"{job_title} Candidate | Immediate Availability",
        f"{candidate_name} – {job_title} Resume Attached",
        f"Sharing {candidate_name}'s Profile for {job_title}",
        f"{job_title} | {candidate_name} | Open to Relocate",
    ]

    return random.choice(subjects)


def build_candidate_summary_text(candidate):
    candidate_name = get_value(candidate, ["full_name", "name"], "Siddhu Kolamala")
    location = get_value(candidate, ["current_location", "location"], "New York, NY")
    open_to_relocate = get_value(candidate, ["open_to_relocate", "relocation"], "Yes")
    work_auth = get_value(candidate, ["work_authorization", "visa"], "")
    experience = get_value(candidate, ["total_experience", "experience"], "")
    availability = get_value(candidate, ["availability"], "Immediate")
    candidate_email = get_value(candidate, ["email"], "siddhukolamala24@gmail.com")
    phone = get_value(candidate, ["phone", "mobile"], "+1 973-687-9494")
    linkedin = get_value(candidate, ["linkedin", "linkedin_url"], "http://linkedin.com/in/kolamala-siddhu")

    lines = []

    if is_valid_value(candidate_name):
        lines.append(f"Name: {candidate_name}")
    if is_valid_value(location):
        lines.append(f"Location: {location}")
    if is_valid_value(open_to_relocate):
        lines.append(f"Open to Relocate: {open_to_relocate}")
    if is_valid_value(work_auth):
        lines.append(f"Work Authorization: {work_auth}")
    if is_valid_value(experience):
        lines.append(f"Experience: {experience}")
    if is_valid_value(availability):
        lines.append(f"Availability: {availability}")
    if is_valid_value(candidate_email):
        lines.append(f"Email: {candidate_email}")
    if is_valid_value(phone):
        lines.append(f"Phone: {phone}")
    if is_valid_value(linkedin):
        lines.append(f"LinkedIn: {linkedin}")

    return "\n".join(lines)


def build_candidate_summary_html(candidate):
    candidate_name = get_value(candidate, ["full_name", "name"], "Siddhu Kolamala")
    location = get_value(candidate, ["current_location", "location"], "New York, NY")
    open_to_relocate = get_value(candidate, ["open_to_relocate", "relocation"], "Yes")
    work_auth = get_value(candidate, ["work_authorization", "visa"], "")
    experience = get_value(candidate, ["total_experience", "experience"], "")
    availability = get_value(candidate, ["availability"], "Immediate")
    candidate_email = get_value(candidate, ["email"], "siddhukolamala24@gmail.com")
    phone = get_value(candidate, ["phone", "mobile"], "+1 973-687-9494")
    linkedin = get_value(candidate, ["linkedin", "linkedin_url"], "http://linkedin.com/in/kolamala-siddhu")

    rows = []

    def add(label, value):
        if is_valid_value(value):
            rows.append(f"<b>{escape(label)}:</b> {escape(value)}<br>")

    add("Name", candidate_name)
    add("Location", location)
    add("Open to Relocate", open_to_relocate)
    add("Work Authorization", work_auth)
    add("Experience", experience)
    add("Availability", availability)
    add("Email", candidate_email)
    add("Phone", phone)
    add("LinkedIn", linkedin)

    return "\n".join(rows)


def generate_body(
    candidate,
    job_role="Marketing Role",
    recruiter_name="",
    post_url="",
    recruiter_email="",
    post_id="",
    requirement_details=""
):
    greeting = get_recruiter_greeting(recruiter_name)
    candidate_name = get_value(candidate, ["full_name", "name"], "Siddhu Kolamala")
    candidate_summary = build_candidate_summary_text(candidate)
    requirement_details = clean_requirement_details(requirement_details)
    post_url = clean_post_url(post_url)

    requirement_section = ""
    if requirement_details:
        requirement_section = f"""

Requirement Snapshot:

{requirement_details}
"""

    post_section = ""
    if post_url:
        post_section = f"""

LinkedIn Post:
{post_url}
"""

    body = f"""
{greeting}

I hope you are doing well.

I came across your recent requirement for {shorten_role(job_role)} and wanted to share {candidate_name}'s profile for your review.

Candidate Summary:

{candidate_summary}

I have attached the updated resume aligned with the requirement.

{requirement_section}
{post_section}

Please let me know if this profile looks suitable for your open role.

Thank you.

Best regards,
Alok Jha
Email: rahuljha1229@gmail.com
""".strip()

    return remove_bad_lines(body)


def generate_html_body(
    candidate,
    job_role="Marketing Role",
    recruiter_name="",
    post_url="",
    recruiter_email="",
    post_id="",
    requirement_details=""
):
    greeting = get_recruiter_greeting(recruiter_name)
    candidate_name = get_value(candidate, ["full_name", "name"], "Siddhu Kolamala")
    candidate_summary_html = build_candidate_summary_html(candidate)
    requirement_details = clean_requirement_details(requirement_details)
    post_url = clean_post_url(post_url)

    requirement_section = ""
    if requirement_details:
        requirement_section = f"""
<p><b>Requirement Snapshot:</b></p>
<div style="background:#f7f9fc; padding:12px; border-left:4px solid #0a66c2; white-space:pre-wrap;">
{escape(requirement_details)}
</div>
"""

    post_section = ""
    if post_url:
        post_section = f"""
<p><b>LinkedIn Post:</b><br>
<a href="{escape(post_url)}" target="_blank">{escape(post_url)}</a></p>
"""

    html = f"""
<html>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #222; line-height: 1.6;">

<p>{escape(greeting)}</p>

<p>I hope you are doing well.</p>

<p>
I came across your recent requirement for <b>{escape(shorten_role(job_role))}</b> and wanted to share {escape(candidate_name)}'s profile for your review.
</p>

<p><b>Candidate Summary:</b></p>

<p>
{candidate_summary_html}
</p>

<p>I have attached the updated resume aligned with the requirement.</p>

{requirement_section}

{post_section}

<p>Please let me know if this profile looks suitable for your open role.</p>

<p>Thank you.</p>

<p>
Best regards,<br>
<b>Alok Jha</b><br>
Email: rahuljha1229@gmail.com
</p>

</body>
</html>
""".strip()

    return html.strip()


def generate_email_body(lead, candidate):
    recruiter_name = get_value(lead, ["recruiter_name", "name", "recruiter"], "")
    recruiter_email = get_value(lead, ["emails", "email", "recruiter_email"], "")
    job_title = get_value(lead, ["job_title", "job_role", "keyword", "role"], "Marketing Role")
    post_url = get_value(lead, ["post_url", "linkedin_post_url", "url"], "")

    requirement_details = get_value(
        lead,
        ["full_post_text", "requirement_details", "jd", "job_description", "post_snippet"],
        ""
    )

    return generate_body(
        candidate=candidate,
        job_role=job_title,
        recruiter_name=recruiter_name,
        recruiter_email=recruiter_email,
        post_url=post_url,
        requirement_details=requirement_details,
    )


def generate_email_html_body(lead, candidate):
    recruiter_name = get_value(lead, ["recruiter_name", "name", "recruiter"], "")
    recruiter_email = get_value(lead, ["emails", "email", "recruiter_email"], "")
    job_title = get_value(lead, ["job_title", "job_role", "keyword", "role"], "Marketing Role")
    post_url = get_value(lead, ["post_url", "linkedin_post_url", "url"], "")

    requirement_details = get_value(
        lead,
        ["full_post_text", "requirement_details", "jd", "job_description", "post_snippet"],
        ""
    )

    return generate_html_body(
        candidate=candidate,
        job_role=job_title,
        recruiter_name=recruiter_name,
        recruiter_email=recruiter_email,
        post_url=post_url,
        requirement_details=requirement_details,
    )