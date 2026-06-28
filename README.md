
# 🤖 AI LinkedIn Recruiter Outreach Automation

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Selenium-Automation-43B02A?style=for-the-badge&logo=selenium"/>
  <img src="https://img.shields.io/badge/Gmail-API-EA4335?style=for-the-badge&logo=gmail"/>
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge"/>
</p>

<p align="center">
<b>Automate recruiter outreach from LinkedIn using AI-powered resume customization and Gmail API.</b>
</p>

---

## 🚀 Overview

This project automates the complete recruiter outreach workflow:

```text
LinkedIn Hiring Posts
        │
        ▼
Recruiter Email Extraction
        │
        ▼
Job Description Extraction
        │
        ▼
AI Resume Customization
        │
        ▼
Professional Email Generation
        │
        ▼
Gmail API Sending
        │
        ▼
Tracking & Duplicate Detection
```

Instead of manually searching jobs, finding recruiter emails, editing resumes, writing emails, and tracking submissions, this tool automates the entire process.

---

# ✨ Features

- 🔍 LinkedIn Hiring Post Scraper
- 📧 Recruiter Email Extraction
- 📄 Full Job Description Extraction
- 🤖 AI Resume Customization (JD Based)
- 📨 Professional Email Generation
- 📎 Automatic Resume Attachment
- 📬 Gmail API (Draft / Send)
- 📊 CSV Lead Management
- 🚫 Duplicate Email Detection
- 📈 Sent Email Tracking

---

# 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Core Automation |
| Selenium | LinkedIn Scraping |
| Gmail API | Email Automation |
| python-docx | Resume Editing |
| docx2pdf | PDF Generation |
| Pandas | CSV Management |

---

# 📁 Project Structure

```text
AI-linkedin-recruiter-outreach-automation/
│
├── main.py
├── config.py
├── candidate_data.json
├── requirements.txt
│
├── src/
│   ├── linkedin_scraper.py
│   ├── gmail_service.py
│   ├── resume_customizer.py
│   ├── email_template.py
│   └── csv_manager.py
│
├── outputs/
├── templates/
├── resumes/
├── credentials/
└── README.md
```

---

# ⚡ Quick Start

```bash
git clone https://github.com/Alokjha16/AI-linkedin-recruiter-outreach-automation.git

cd AI-linkedin-recruiter-outreach-automation

pip install -r requirements.txt
```

Run in Draft Mode

```bash
python main.py
```

Send Emails

```bash
python main.py --send
```

Skip Scraping

```bash
python main.py --skip-scrape
```

Custom Keywords

```bash
python main.py --keywords "Hiring Python Developer" --max-emails 10
```

---

# 📤 Output

```
outputs/
├── leads.csv
├── sent_log.csv
└── resumes/
    └── custom_resume.pdf
```

---

# 🎯 Use Cases

- Candidate Marketing
- Recruiter Outreach
- Staffing Agencies
- Job Search Automation
- Resume Personalization

---

# 🚀 Future Improvements

- AI Cover Letter Generation
- Recruiter Response Tracking
- Campaign Dashboard
- Multi-Candidate Support
- AI Lead Scoring

---

# 👨‍💻 Author

**Alok Jha**

- GitHub: https://github.com/Alokjha16
- LinkedIn: https://linkedin.com/in/alokjha16

---

## ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

<p align="center">
Made with ❤️ using Python, Selenium & Gmail API
</p>
