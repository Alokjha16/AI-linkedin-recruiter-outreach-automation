
<div align="center">

# 🚀 AI LinkedIn Recruiter Outreach Automation

### **Scrape Recruiters • Customize Resume • Send Personalized Emails**

<p>
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white">
<img src="https://img.shields.io/badge/Gmail_API-EA4335?style=for-the-badge&logo=gmail&logoColor=white">
<img src="https://img.shields.io/badge/AI-Resume_Customization-7B61FF?style=for-the-badge">
<img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge">
</p>

**Automate the complete recruiter outreach workflow — from LinkedIn hiring posts to personalized recruiter emails with AI-customized resumes.**

</div>

---

## ✨ Highlights

- 🔍 Scrapes recent LinkedIn hiring posts
- 📧 Extracts recruiter email addresses
- 📄 Extracts complete Job Descriptions
- 🤖 AI customizes resume based on every JD
- 📨 Generates personalized outreach emails
- 📎 Attaches customized PDF resume
- 📬 Sends emails using Gmail API
- 📊 Tracks sent emails & prevents duplicates

---

## ⚡ Workflow

```text
LinkedIn Hiring Posts
        │
        ▼
Recruiter Email Extraction
        │
        ▼
Full Job Description
        │
        ▼
AI Resume Customization
        │
        ▼
Professional Email Generation
        │
        ▼
Gmail API
        │
        ▼
Tracking & Deduplication
```

---

## 🛠 Tech Stack

| Category | Tools |
|----------|------|
| Language | Python |
| Web Automation | Selenium |
| AI Processing | Resume Customization |
| Email | Gmail API |
| Documents | python-docx, docx2pdf |
| Data | Pandas, CSV |

---

## 📂 Project Structure

```text
AI-linkedin-recruiter-outreach-automation/
├── main.py
├── config.py
├── candidate_data.json
├── requirements.txt
├── src/
│   ├── linkedin_scraper.py
│   ├── gmail_service.py
│   ├── resume_customizer.py
│   ├── email_template.py
│   └── csv_manager.py
├── templates/
├── resumes/
├── outputs/
└── credentials/
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/Alokjha16/AI-linkedin-recruiter-outreach-automation.git

cd AI-linkedin-recruiter-outreach-automation

pip install -r requirements.txt
```

### Run (Draft Mode)

```bash
python main.py
```

### Live Send

```bash
python main.py --send
```

### Skip Scraping

```bash
python main.py --skip-scrape
```

### Custom Search

```bash
python main.py --keywords "Hiring Python Developer" --max-emails 20
```

---

## 📦 Outputs

```text
outputs/
├── leads.csv
├── sent_log.csv
└── resumes/
    └── custom_resume.pdf
```

---

## 🌟 Key Features

| ✅ | Description |
|---|---|
| LinkedIn Scraping | Collects hiring posts |
| Email Extraction | Finds recruiter emails |
| JD Parsing | Reads full job descriptions |
| Resume Personalization | Tailors resume for each role |
| Gmail Automation | Drafts or sends emails |
| Duplicate Protection | Prevents repeated outreach |
| CSV Tracking | Maintains lead & sent logs |

---

## 🗺️ Roadmap

- [x] LinkedIn Scraping
- [x] Gmail API Integration
- [x] Resume Customization
- [x] Duplicate Detection
- [ ] AI Cover Letter
- [ ] Campaign Analytics Dashboard
- [ ] Recruiter Reply Tracking
- [ ] Multi-Candidate Support

---

## 👨‍💻 Author

**Alok Jha**

GitHub: https://github.com/Alokjha16

LinkedIn: https://linkedin.com/in/alokjha16

---

<div align="center">

### ⭐ If you found this project useful, please consider giving it a Star!

Made with ❤️ using Python, Selenium & Gmail API

</div>
