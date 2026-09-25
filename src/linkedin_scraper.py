"""
linkedin_scraper.py - LinkedIn Post Scraper Module
Optimized for Marketing / SEO / PPC recruiter email scraping.
"""

import time
import random
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    WebDriverException,
)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    MIN_ACTION_DELAY,
    MAX_ACTION_DELAY,
    MAX_POSTS_PER_KEYWORD,
    MAX_SCROLL_ATTEMPTS,
    CHROME_PROFILE_DIR,
    HEADLESS_MODE,
    SCREENSHOTS_DIR,
)

from src.email_extractor import extract_emails

logger = logging.getLogger(__name__)

EFFECTIVE_MAX_POSTS_PER_KEYWORD = 50  # LinkedIn-only scale mode: process up to 50 visible posts per keyword

BLOCKED_TERMS = [
    "training and placement",
    "placement support",
    "job support",
    "proxy interview",
    "fake profile",
    "pay after placement",
    "100% placement",
    "consultancy fees",
    "course fee",
    "paid training",
    "we provide professional marketing",
    "bench sales",
    "hotlist",
    "hot list",
    "vendor list",
    "available candidates",
    "available consultants",
    "share hotlist",
    "requirements & hotlist",
    "requirements and hotlist",
    "hire-bangladesh",
    "hire-india",
    "hire-pakistan",
]

PAGE_DUMP_TERMS = [
    "skip to search",
    "skip to main content",
    "try premium",
    "linkedin news",
    "messaging",
    "notifications",
    "my network",
    "for business",
    "are these results helpful",
    "your feedback helps us improve",
    "linkedin corporation",
    "privacy & terms",
]

MARKETING_TERMS = [
    "seo",
    "seo specialist",
    "seo executive",
    "seo analyst",
    "digital marketing",
    "digital marketer",
    "marketing specialist",
    "marketing executive",
    "marketing coordinator",
    "ppc",
    "google ads",
    "paid search",
    "sem",
    "performance marketing",
    "growth marketing",
    "content marketing",
    "email marketing",
    "marketing automation",
    "social media",
    "lead generation",
    "demand generation",
]


def _random_delay(min_sec: float = MIN_ACTION_DELAY, max_sec: float = MAX_ACTION_DELAY) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def create_driver() -> webdriver.Chrome:
    chrome_options = Options()

    if HEADLESS_MODE:
        chrome_options.add_argument("--headless=new")

    if CHROME_PROFILE_DIR:
        chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--remote-debugging-port=0")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(4)

    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass

    logger.info("Chrome WebDriver initialized successfully.")
    return driver


def driver_is_alive(driver: webdriver.Chrome) -> bool:
    """Return False when Selenium/Chrome session is dead."""
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


def restart_driver(old_driver: Optional[webdriver.Chrome] = None) -> webdriver.Chrome:
    """Safely restart Chrome driver and verify LinkedIn session again."""
    try:
        if old_driver:
            old_driver.quit()
    except Exception:
        pass

    new_driver = create_driver()
    wait_for_manual_login(new_driver)
    return new_driver


def wait_for_manual_login(driver: webdriver.Chrome) -> bool:
    driver.get("https://www.linkedin.com/feed/")
    logger.info("LinkedIn opened. Checking login session...")

    print("\n" + "=" * 60)
    print("  LINKEDIN LOGIN CHECK")
    print("=" * 60)
    print("If login page opens, login manually once.")
    print("After login, script will auto-detect feed. No Enter needed.")
    print("=" * 60)

    login_selectors = (
        "input[placeholder*='Search'], "
        "input.search-global-typeahead__input, "
        "a[href*='/feed/'], "
        "a[href*='/mynetwork/'], "
        "img.global-nav__me-photo, "
        ".global-nav, "
        ".scaffold-layout"
    )

    start_time = time.time()
    max_wait_seconds = 180

    while time.time() - start_time < max_wait_seconds:
        try:
            current_url = driver.current_url.lower()

            if "login" not in current_url and "checkpoint" not in current_url:
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, login_selectors))
                    )
                    logger.info("LinkedIn login verified successfully.")
                    print("✅ LinkedIn login detected automatically!\n")
                    return True
                except TimeoutException:
                    pass

            print("⏳ Waiting for LinkedIn login/session...")
            time.sleep(5)

        except Exception:
            time.sleep(5)

    print("⚠️ Could not verify LinkedIn login. Proceeding anyway...\n")
    return True


def build_search_urls(keyword: str) -> List[str]:
    encoded_keyword = quote_plus(keyword)

    strict_url = (
        "https://www.linkedin.com/search/results/content/"
        f"?keywords={encoded_keyword}"
        f"&datePosted=%22past-24h%22"
        f"&geoUrn=%5B%22103644278%22%5D"
        f"&origin=FACETED_SEARCH"
        f"&sortBy=%22date_posted%22"
    )

    no_geo_url = (
        "https://www.linkedin.com/search/results/content/"
        f"?keywords={encoded_keyword}"
        f"&datePosted=%22past-24h%22"
        f"&origin=FACETED_SEARCH"
        f"&sortBy=%22date_posted%22"
    )

    broad_url = (
        "https://www.linkedin.com/search/results/content/"
        f"?keywords={encoded_keyword}"
        f"&origin=GLOBAL_SEARCH_HEADER"
        f"&sortBy=%22date_posted%22"
    )

    return [strict_url, no_geo_url, broad_url]


def search_posts(driver: webdriver.Chrome, keyword: str, attempt: int = 0) -> None:
    urls = build_search_urls(keyword)
    attempt = min(attempt, len(urls) - 1)

    logger.info(f"Searching LinkedIn posts for: {keyword} | attempt={attempt + 1}")
    driver.get(urls[attempt])
    _random_delay(3, 5)


def page_has_no_results(driver: webdriver.Chrome) -> bool:
    try:
        text = driver.find_element(By.TAG_NAME, "body").text.lower()
    except Exception:
        return False

    no_result_terms = [
        "no results found",
        "try shortening or rephrasing your search",
        "no matching results",
        "we couldn’t find any results",
        "we couldn't find any results",
    ]

    return any(term in text for term in no_result_terms)


def scroll_and_load_posts(driver: webdriver.Chrome) -> None:
    last_height = 0

    for _ in range(MAX_SCROLL_ATTEMPTS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        _random_delay(1.0, 1.8)

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break

        last_height = new_height


def click_see_more_buttons(driver: webdriver.Chrome, root=None, limit=20) -> None:
    search_root = root if root is not None else driver

    xpaths = [
        ".//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see more')]",
        ".//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see more')]/ancestor::button",
        ".//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
        ".//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]/ancestor::button",
    ]

    clicked = 0

    for xpath in xpaths:
        try:
            buttons = search_root.find_elements(By.XPATH, xpath)

            for btn in buttons[:limit]:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.15)
                        driver.execute_script("arguments[0].click();", btn)
                        clicked += 1
                        time.sleep(0.2)
                except (StaleElementReferenceException, ElementClickInterceptedException):
                    continue
                except Exception:
                    continue

        except Exception:
            continue

    if clicked:
        logger.info(f"Clicked {clicked} see-more buttons.")


def looks_like_page_dump(text: str) -> bool:
    text = str(text or "").strip()
    low = text.lower()

    if not text:
        return False

    if len(text) > 9000:
        return True

    bad_count = sum(1 for term in PAGE_DUMP_TERMS if term in low)

    if bad_count >= 4 and len(text) > 2500:
        return True

    if bad_count >= 6:
        return True

    if "are these results helpful" in low and "your feedback helps us improve" in low and len(text) > 1800:
        return True

    return False


def is_reaction_or_engagement_line(line: str) -> bool:
    low = str(line or "").strip().lower()

    if not low:
        return True

    patterns = [
        r"^\d+\s+reaction[s]?$",
        r"^\d+\s+comment[s]?$",
        r"^\d+\s+repost[s]?$",
        r"^\d+\s+share[s]?$",
        r"^\d+\s+like[s]?$",
        r"^\d+\s+impression[s]?$",
        r"^like$",
        r"^comment$",
        r"^repost$",
        r"^send$",
        r"^share$",
        r"^\u2026\s*more$",
        r"^\.\.\.\s*more$",
    ]

    return any(re.fullmatch(pattern, low) for pattern in patterns)


def clean_post_text(text: str, keep_newlines: bool = False) -> str:
    text = str(text or "")
    text = text.replace("\r", "\n").replace("\t", " ")

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    junk_exact = {
        "home",
        "my network",
        "jobs",
        "messaging",
        "notifications",
        "me",
        "for business",
        "try premium",
        "try premium for ₹0",
        "start premium",
        "posts",
        "latest",
        "past 24 hours",
        "content type",
        "from member",
        "all filters",
        "reset",
        "feed post",
        "like",
        "comment",
        "share",
        "repost",
        "send",
        "see more",
        "show more",
        "follow",
        "join",
        "connect",
        "are these results helpful?",
        "your feedback helps us improve search results",
        "about",
        "accessibility",
        "help center",
        "privacy & terms",
        "ad choices",
        "advertising",
        "business services",
        "get the linkedin app",
        "more",
    }

    cleaned_lines = []

    for line in lines:
        low = line.lower().strip()

        if is_reaction_or_engagement_line(line):
            continue

        if low in junk_exact:
            continue

        if re.fullmatch(r"\d+", low):
            continue

        if "notifications home my network jobs messaging" in low:
            continue

        if "skip to search" in low or "skip to main content" in low:
            continue

        if "linkedin corporation" in low:
            continue

        cleaned_lines.append(line)

    if keep_newlines:
        cleaned = "\n".join(cleaned_lines)
    else:
        cleaned = " ".join(cleaned_lines)

    cleaned = "\n".join([" ".join(line.split()) for line in cleaned.splitlines()])
    cleaned = " ".join(cleaned.split()) if not keep_newlines else cleaned

    return cleaned.strip()


def is_blocked_post(text: str) -> bool:
    text_lower = str(text).lower()
    return any(term in text_lower for term in BLOCKED_TERMS)


def is_relevant_job_post(text: str, keyword: str) -> bool:
    low = str(text).lower()

    if not extract_emails(text):
        return False

    negative_terms = [
        "available candidates",
        "available consultants",
        "hotlist",
        "bench sales",
        "vendor list",
        "share hotlist",
    ]

    if any(term in low for term in negative_terms):
        return False

    positive_terms = [
        "hiring",
        "requirement",
        "requirements",
        "looking for",
        "need",
        "urgent",
        "role",
        "position",
        "opening",
        "opportunity",
        "contract",
        "remote",
        "onsite",
        "hybrid",
        "send resume",
        "share resume",
        "interested candidates",
        "email resume",
    ] + MARKETING_TERMS

    if any(term in low for term in positive_terms):
        return True

    keyword_words = [w for w in keyword.lower().split() if len(w) > 2 and w not in {"email", "hiring"}]
    matched_words = [w for w in keyword_words if w in low]

    return len(matched_words) >= 1


def find_post_elements(driver: webdriver.Chrome):
    selectors = [
        "li.reusable-search__result-container",
        "div.reusable-search__result-container",
        "div.entity-result",
        "li div.entity-result",
        "ul.reusable-search__entity-result-list > li",
        "div[data-urn*='urn:li:activity']",
        "div.feed-shared-update-v2",
        "article",
    ]

    elements = []
    seen_keys = set()

    def add_element(el):
        try:
            txt = (el.text or "").strip()
            if len(txt) < 40:
                return

            low = txt.lower()

            if "@" not in txt and len(txt) < 120:
                return

            if "are these results helpful" in low and "your feedback helps us improve" in low and "@" not in txt:
                return

            key = el.id
            if key not in seen_keys:
                seen_keys.add(key)
                elements.append(el)

        except Exception:
            return

    for selector in selectors:
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, selector):
                add_element(el)
        except Exception:
            continue

    try:
        js_elements = driver.execute_script(
            """
            const emailRegex = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}/i;
            const usefulWords = /(hiring|requirement|need|looking|contract|remote|hybrid|onsite|role|position|opening|seo|digital marketing|ppc|google ads|sem|performance marketing|growth marketing|content marketing|email marketing|marketing automation|social media|lead generation)/i;
            const nodes = Array.from(document.querySelectorAll('li, article, div'));
            const out = [];

            for (const node of nodes) {
                const txt = (node.innerText || '').trim();
                if (!txt) continue;
                if (txt.length < 80 || txt.length > 6500) continue;
                if (!emailRegex.test(txt)) continue;
                if (!usefulWords.test(txt)) continue;

                const rect = node.getBoundingClientRect();
                if (rect.width < 250 || rect.height < 80) continue;

                out.push(node);
                if (out.length >= 60) break;
            }
            return out;
            """
        )

        for el in js_elements or []:
            add_element(el)

    except Exception:
        pass

    return elements


def get_recruiter_name(post_el, post_text: str) -> str:
    selectors = [
        ".update-components-actor__name span[aria-hidden='true']",
        ".feed-shared-actor__name span[aria-hidden='true']",
        ".entity-result__title-text span[aria-hidden='true']",
        ".entity-result__title-text a span[dir='ltr']",
        "span.update-components-actor__name",
        "span.feed-shared-actor__name",
        "a.update-components-actor__meta-link span[dir='ltr']",
        "a.feed-shared-actor__container-link span[dir='ltr']",
        "a.app-aware-link[href*='/in/'] span[dir='ltr']",
        "a[href*='/in/'] span[dir='ltr']",
    ]

    bad_fragments = [
        "try premium",
        "premium for",
        "follow",
        "join",
        "connect",
        "message",
        "view profile",
        "linkedin",
        "posted",
        "repost",
        "like",
        "comment",
        "share",
        "send",
        "followers",
        "connections",
        "search",
    ]

    def valid_name(name: str) -> bool:
        name = clean_post_text(name)
        low = name.lower()

        if not name:
            return False
        if any(bad in low for bad in bad_fragments):
            return False
        if "@" in name or "http" in low:
            return False
        if re.fullmatch(r"[\d\s+().-]+", name):
            return False
        if len(name) < 3 or len(name) > 80:
            return False

        words = [w for w in re.split(r"\s+", name) if w]
        if len(words) > 8:
            return False

        return bool(re.search(r"[A-Za-z]", name))

    for selector in selectors:
        try:
            els = post_el.find_elements(By.CSS_SELECTOR, selector)

            for name_el in els:
                name = clean_post_text(name_el.text)
                if valid_name(name):
                    return name[:80]

        except Exception:
            continue

    lines = [line.strip() for line in str(post_text or "").splitlines() if line.strip()]

    for line in lines[:15]:
        line = clean_post_text(line)

        if valid_name(line):
            return line[:80]

    return "LinkedIn Recruiter"


def get_profile_link(post_el) -> str:
    selectors = [
        "a.update-components-actor__meta-link",
        "a.feed-shared-actor__container-link",
        "a.app-aware-link[href*='/in/']",
        "a[href*='linkedin.com/in/']",
    ]

    for selector in selectors:
        try:
            link_el = post_el.find_element(By.CSS_SELECTOR, selector)
            href = link_el.get_attribute("href") or ""

            if href and "/in/" in href:
                return href.split("?")[0]

        except Exception:
            continue

    return ""


def normalize_post_url(url: str) -> str:
    url = str(url or "").strip()

    if not url:
        return ""

    if "urn:li:activity:" in url and "/feed/update/" not in url:
        match = re.search(r"urn:li:activity:\d+", url)
        if match:
            return f"https://www.linkedin.com/feed/update/{match.group(0)}/"

    return url.split("?")[0]


def is_valid_post_url(url: str) -> bool:
    url = str(url or "").lower()
    return (
        "/feed/update/" in url
        or "urn:li:activity" in url
        or "/posts/" in url
        or "activity-" in url
    ) and "/in/" not in url


def get_post_url(post_el) -> str:
    try:
        data_urn = post_el.get_attribute("data-urn") or ""
        if "urn:li:activity:" in data_urn:
            return normalize_post_url(data_urn)
    except Exception:
        pass

    try:
        descendants = post_el.find_elements(By.CSS_SELECTOR, "[data-urn*='urn:li:activity']")
        for d in descendants:
            data_urn = d.get_attribute("data-urn") or ""
            if "urn:li:activity:" in data_urn:
                return normalize_post_url(data_urn)
    except Exception:
        pass

    selectors = [
        "a[href*='/feed/update/urn:li:activity']",
        "a[href*='urn:li:activity']",
        "a[href*='/posts/']",
        "a[href*='activity-']",
        "a[href*='/pulse/']",
    ]

    for selector in selectors:
        try:
            links = post_el.find_elements(By.CSS_SELECTOR, selector)

            for link_el in links:
                href = link_el.get_attribute("href") or ""
                href = href.strip()

                if href and is_valid_post_url(href):
                    return normalize_post_url(href)

        except Exception:
            continue

    return ""


def get_post_time(post_el) -> str:
    selectors = [
        ".update-components-actor__sub-description span",
        ".feed-shared-actor__sub-description",
        "time",
    ]

    for selector in selectors:
        try:
            time_el = post_el.find_element(By.CSS_SELECTOR, selector)
            text = clean_post_text(time_el.text)

            if text:
                return text[:50]

        except Exception:
            continue

    return "Recent"


def detect_location(text: str) -> str:
    low = str(text).lower()

    if "remote" in low:
        return "Remote"
    if "new york" in low or re.search(r"\bny\b", low):
        return "New York, NY"
    if "chicago" in low or re.search(r"\bil\b", low):
        return "Chicago, IL"
    if "texas" in low or re.search(r"\btx\b", low):
        return "Texas"
    if "california" in low or re.search(r"\bca\b", low):
        return "California"
    if "new jersey" in low or re.search(r"\bnj\b", low):
        return "New Jersey"
    if "virginia" in low or re.search(r"\bva\b", low):
        return "Virginia"
    if "florida" in low or re.search(r"\bfl\b", low):
        return "Florida"
    if "united states" in low or "usa" in low or " us " in f" {low} ":
        return "United States"

    return "United States"


def detect_post_type(text: str) -> str:
    low = str(text).lower()

    if "bench sales" in low or "bench sale" in low:
        return "Bench Sales"
    if "hotlist" in low or "hot list" in low or "hotlists" in low:
        return "Hotlist"
    if "vendor list" in low or "vendor" in low:
        return "Vendor"
    if "w2" in low or "w-2" in low:
        return "W2"
    if "c2c" in low or "corp to corp" in low:
        return "C2C"
    if "contract" in low:
        return "Contract"

    return "Recruiter Post"


def get_text_from_element(driver, element) -> str:
    try:
        click_see_more_buttons(driver, root=element, limit=3)
    except Exception:
        pass

    text_selectors = [
        ".update-components-text",
        ".feed-shared-inline-show-more-text",
        ".feed-shared-update-v2__description",
        ".entity-result__content",
        ".entity-result__summary",
        ".entity-result__primary-subtitle",
        ".entity-result__secondary-subtitle",
    ]

    texts = []

    for selector in text_selectors:
        try:
            els = element.find_elements(By.CSS_SELECTOR, selector)

            for el in els:
                txt = driver.execute_script("return arguments[0].innerText;", el) or el.text
                txt = clean_post_text(txt, keep_newlines=True)

                if txt and not looks_like_page_dump(txt):
                    texts.append(txt)

        except Exception:
            continue

    try:
        full_card_text = driver.execute_script("return arguments[0].innerText;", element) or element.text
        full_card_text = clean_post_text(full_card_text, keep_newlines=True)

        if full_card_text and not looks_like_page_dump(full_card_text):
            texts.append(full_card_text)

    except Exception:
        pass

    if not texts:
        return ""

    def score_text(txt: str) -> int:
        low = txt.lower()
        score = 0
        score += 25 if extract_emails(txt) else 0
        score += 10 if "hiring" in low else 0
        score += 8 if "requirement" in low else 0
        score += 8 if any(term in low for term in MARKETING_TERMS) else 0
        score += 5 if "contract" in low else 0
        score += 5 if "remote" in low else 0
        score += min(len(txt), 2500) // 100
        score -= 25 if looks_like_page_dump(txt) else 0
        return score

    best = max(texts, key=score_text)

    if len(best) > 3500:
        best = extract_single_email_block(best, "")

    if len(best) > 3200:
        best = best[:3200].rsplit("\n", 1)[0].strip()

    return best.strip()


def get_detail_page_text(driver: webdriver.Chrome, post_url: str) -> str:
    if not is_valid_post_url(post_url):
        return ""

    original_window = driver.current_window_handle

    try:
        driver.execute_script("window.open(arguments[0], '_blank');", post_url)
        time.sleep(1.2)

        driver.switch_to.window(driver.window_handles[-1])
        _random_delay(1.8, 2.5)

        click_see_more_buttons(driver, limit=5)
        _random_delay(0.5, 0.8)

        selectors = [
            "div[data-urn*='urn:li:activity'] .update-components-text",
            "div[data-urn*='urn:li:activity'] .feed-shared-inline-show-more-text",
            ".feed-shared-update-v2 .update-components-text",
            ".feed-shared-update-v2 .feed-shared-inline-show-more-text",
            ".update-components-text",
            ".feed-shared-inline-show-more-text",
        ]

        texts = []

        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)

                for el in elements:
                    try:
                        txt = driver.execute_script("return arguments[0].innerText;", el) or el.text
                        txt = clean_post_text(txt, keep_newlines=True)

                        if txt and not looks_like_page_dump(txt):
                            texts.append(txt)

                    except Exception:
                        continue

            except Exception:
                continue

        if not texts:
            return ""

        return max(texts, key=len)

    except Exception as e:
        logger.warning(f"Could not fetch detail page text: {e}")
        return ""

    finally:
        try:
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(original_window)
        except Exception:
            pass


def extract_single_email_block(text: str, keyword: str) -> str:
    text = clean_post_text(text, keep_newlines=True)

    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    emails = extract_emails(text)

    if not emails:
        return text

    email_positions = []

    for idx, line in enumerate(lines):
        if extract_emails(line):
            email_positions.append(idx)

    if not email_positions:
        return text

    keyword_words = [w.lower() for w in keyword.split() if len(w) > 2]

    best_block = ""
    best_score = -1

    for email_idx in email_positions:
        start = max(0, email_idx - 28)
        end = min(len(lines), email_idx + 12)

        block_lines = lines[start:end]

        while block_lines and (
            "try premium" in block_lines[0].lower()
            or re.fullmatch(r"\d+", block_lines[0].lower())
            or "3rd+" in block_lines[0].lower()
            or block_lines[0].lower() in {"follow", "join", "connect"}
        ):
            block_lines.pop(0)

        block = "\n".join(block_lines)
        low = block.lower()

        score = 0
        score += sum(3 for w in keyword_words if w in low)
        score += 6 if "hiring" in low else 0
        score += 6 if "requirement" in low else 0
        score += 6 if any(term in low for term in MARKETING_TERMS) else 0
        score += 3 if "location" in low else 0
        score += 3 if "experience" in low else 0
        score += 3 if "interested" in low or "share" in low else 0
        score -= 10 if "try premium" in low else 0
        score -= 10 if "are these results helpful" in low else 0

        if score > best_score:
            best_score = score
            best_block = block

    best_block = clean_post_text(best_block, keep_newlines=True)

    if len(best_block) > 3000:
        best_block = best_block[:3000].rsplit("\n", 1)[0].strip()

    return best_block


def choose_best_text(base_text: str, detail_text: str, keyword: str) -> str:
    base_clean = clean_post_text(base_text, keep_newlines=True)
    detail_clean = clean_post_text(detail_text, keep_newlines=True)

    candidates = []

    for txt in [base_clean, detail_clean]:
        if txt and not looks_like_page_dump(txt):
            candidates.append(txt)

    if not candidates:
        if base_clean:
            return extract_single_email_block(base_clean, keyword)
        if detail_clean:
            return extract_single_email_block(detail_clean, keyword)
        return ""

    best = max(candidates, key=len)

    if len(best) > 3500 or len(extract_emails(best)) > 2:
        best = extract_single_email_block(best, keyword)

    return best.strip()


def calculate_lead_score(text: str, keyword: str) -> int:
    low = str(text or "").lower()
    score = 45

    positive_weights = {
        "hiring": 18,
        "requirement": 16,
        "requirements": 16,
        "need": 12,
        "looking for": 14,
        "role": 8,
        "position": 8,
        "opening": 10,
        "opportunity": 8,
        "remote": 8,
        "contract": 8,
        "immediate": 6,
        "share resume": 12,
        "send resume": 12,
        "email": 6,
        "seo": 22,
        "seo specialist": 24,
        "seo executive": 22,
        "digital marketing": 22,
        "marketing specialist": 20,
        "marketing executive": 18,
        "marketing coordinator": 18,
        "ppc": 22,
        "google ads": 22,
        "sem": 20,
        "performance marketing": 22,
        "growth marketing": 20,
        "content marketing": 18,
        "email marketing": 18,
        "marketing automation": 18,
        "social media": 18,
        "lead generation": 18,
    }

    negative_weights = {
        "bench sales": 60,
        "bench recruiter": 60,
        "bench marketing": 60,
        "hotlist": 70,
        "hot list": 70,
        "vendor list": 65,
        "available candidates": 65,
        "available consultants": 65,
        "share hotlist": 75,
        "requirements & hotlist": 75,
        "requirements and hotlist": 75,
        "training and placement": 60,
        "placement support": 60,
        "pay after placement": 70,
        "proxy interview": 80,
    }

    for term, weight in positive_weights.items():
        if term in low:
            score += weight

    for term, weight in negative_weights.items():
        if term in low:
            score -= weight

    keyword_words = [
        w for w in str(keyword or "").lower().split()
        if len(w) > 2 and w not in {"email", "hiring", "specialist"}
    ]

    score += sum(5 for w in keyword_words if w in low)

    if extract_emails(text):
        score += 15

    if len(text) < 100:
        score -= 15

    if looks_like_page_dump(text):
        score -= 80

    return max(0, min(100, score))


def _parse_single_post(driver: webdriver.Chrome, post_el, keyword: str, index: int) -> Optional[Dict]:
    raw_text = get_text_from_element(driver, post_el)

    if not raw_text:
        return None

    if not extract_emails(raw_text):
        return None

    profile_link = get_profile_link(post_el)
    post_url = get_post_url(post_el)

    # SPEED MODE:
    # Do not open LinkedIn detail page for each post.
    # The card text is enough for email extraction + resume customization snapshot.
    detail_text = ""

    full_post_text = choose_best_text(raw_text, detail_text, keyword)
    full_post_text = clean_post_text(full_post_text, keep_newlines=True)

    if len(full_post_text) > 3200:
        full_post_text = extract_single_email_block(full_post_text, keyword)

    if len(full_post_text) > 3000:
        full_post_text = full_post_text[:3000].rsplit("\n", 1)[0].strip()

    post_text_compact = clean_post_text(full_post_text)

    if not post_text_compact or len(post_text_compact) < 40:
        return None

    if looks_like_page_dump(post_text_compact):
        logger.info(f"Post #{index + 1}: Page dump detected, skipped.")
        return None

    if is_blocked_post(post_text_compact):
        logger.info(f"Post #{index + 1}: Spam/irrelevant blocked.")
        return None

    emails = extract_emails(post_text_compact)

    if not emails:
        return None

    if not is_relevant_job_post(post_text_compact, keyword):
        logger.info(f"Post #{index + 1}: Not relevant, skipped.")
        return None

    lead_score = calculate_lead_score(post_text_compact, keyword)

    if lead_score < 55:
        logger.info(f"Post #{index + 1}: Low lead score {lead_score}, skipped.")
        return None

    recruiter_name = get_recruiter_name(post_el, raw_text)
    post_time = get_post_time(post_el)
    location = detect_location(post_text_compact)
    post_type = detect_post_type(post_text_compact)

    if not is_valid_post_url(post_url):
        post_url = ""

    return {
        "recruiter_name": recruiter_name,
        "emails": ", ".join(emails),
        "profile_link": profile_link,
        "post_url": post_url,
        "post_time": post_time,
        "post_type": post_type,
        "job_role": keyword,
        "location": location,
        "full_post_text": full_post_text,
        "post_snippet": post_text_compact[:700].strip(),
        "lead_score": lead_score,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _email_context_blocks_from_page(driver: webdriver.Chrome, keyword: str, max_blocks: int = 80) -> List[str]:
    """
    Very fast extraction: collect text blocks containing emails directly from the visible LinkedIn search page.
    This avoids opening every post and is the main speed improvement.
    """
    try:
        blocks = driver.execute_script(
            """
            const nodes = Array.from(document.querySelectorAll('li, article, div'));
            const emailRegex = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i;
            const usefulWords = /(hiring|requirement|requirements|need|looking|role|position|opening|contract|remote|hybrid|onsite|send resume|share resume|email resume|seo|digital marketing|ppc|google ads|sem|performance marketing|growth marketing|content marketing|email marketing|social media|lead generation)/i;
            const out = [];
            const seen = new Set();

            for (const node of nodes) {
                const txt = (node.innerText || '').trim();
                if (!txt) continue;
                if (txt.length < 80 || txt.length > 4500) continue;
                if (!emailRegex.test(txt)) continue;
                if (!usefulWords.test(txt)) continue;

                const rect = node.getBoundingClientRect();
                if (rect.width < 250 || rect.height < 60) continue;

                const compact = txt.replace(/\s+/g, ' ').slice(0, 1200);
                if (seen.has(compact)) continue;
                seen.add(compact);
                out.push(txt);
                if (out.length >= arguments[0]) break;
            }
            return out;
            """,
            max_blocks,
        )
    except Exception:
        blocks = []

    cleaned_blocks = []
    seen = set()

    for block in blocks or []:
        block = clean_post_text(block, keep_newlines=True)
        if not block or looks_like_page_dump(block):
            continue
        block = extract_single_email_block(block, keyword)
        compact = clean_post_text(block)
        if not compact or compact in seen:
            continue
        seen.add(compact)
        cleaned_blocks.append(block)

    return cleaned_blocks


def extract_page_level_leads(driver: webdriver.Chrome, keyword: str) -> List[Dict]:
    """Create lead rows from visible search page blocks without clicking individual posts."""
    leads = []
    seen_emails = set()
    blocks = _email_context_blocks_from_page(driver, keyword)

    for idx, block in enumerate(blocks):
        compact = clean_post_text(block)
        emails = extract_emails(compact)

        if not emails:
            continue
        if is_blocked_post(compact):
            continue
        if not is_relevant_job_post(compact, keyword):
            continue

        lead_score = calculate_lead_score(compact, keyword)
        if lead_score < 40:
            logger.info(f"Page block #{idx + 1}: Low lead score {lead_score}, skipped.")
            continue

        new_emails = []
        for email in emails:
            email_low = email.strip().lower()
            if email_low and email_low not in seen_emails:
                seen_emails.add(email_low)
                new_emails.append(email_low)

        if not new_emails:
            continue

        leads.append({
            "recruiter_name": "LinkedIn Recruiter",
            "emails": ", ".join(new_emails),
            "profile_link": "",
            "post_url": "",
            "post_time": "Recent",
            "post_type": detect_post_type(compact),
            "job_role": keyword,
            "location": detect_location(compact),
            "full_post_text": block[:3000].strip(),
            "post_snippet": compact[:700].strip(),
            "lead_score": lead_score,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    if leads:
        logger.info(f"Fast page-level extraction found {len(leads)} lead(s) for keyword: {keyword}")

    return leads


def extract_post_data(driver: webdriver.Chrome, keyword: str) -> List[Dict]:
    posts_data = []
    seen_email_items = set()

    try:
        click_see_more_buttons(driver, limit=10)
        _random_delay(0.8, 1.4)

        post_elements = find_post_elements(driver)
        logger.info(f"Found {len(post_elements)} potential post elements.")
        logger.info(f"Processing first {EFFECTIVE_MAX_POSTS_PER_KEYWORD} posts for keyword: {keyword}")

        for idx, post_el in enumerate(post_elements[:EFFECTIVE_MAX_POSTS_PER_KEYWORD]):
            try:
                post_info = _parse_single_post(driver, post_el, keyword, idx)

                if post_info and post_info.get("emails"):
                    emails = [e.strip().lower() for e in post_info["emails"].split(",") if e.strip()]
                    new_emails = [e for e in emails if e not in seen_email_items]

                    if not new_emails:
                        logger.info(f"Post #{idx + 1}: Duplicate emails skipped: {post_info['emails']}")
                        continue

                    for e in new_emails:
                        seen_email_items.add(e)

                    post_info["emails"] = ", ".join(new_emails)
                    posts_data.append(post_info)

                    jd_len = len(post_info.get("full_post_text", ""))
                    logger.info(
                        f"Post #{idx + 1}: Found {post_info['post_type']} email(s): {post_info['emails']} | "
                        f"Score: {post_info.get('lead_score', 'NA')} | JD chars: {jd_len} | "
                        f"Recruiter: {post_info.get('recruiter_name', '')}"
                    )

            except StaleElementReferenceException:
                logger.warning(f"Post #{idx + 1}: Element stale, skipping.")
            except Exception as e:
                logger.warning(f"Post #{idx + 1}: Error parsing — {e}")

    except Exception as e:
        logger.error(f"Error extracting posts: {e}")

    return posts_data


def scrape_keyword_with_fallback(driver: webdriver.Chrome, keyword: str) -> List[Dict]:
    labels = [
        "US + Past 24h",
        "Past 24h",
        "Broad recent",
    ]

    all_attempt_posts = []
    seen_attempt_emails = set()

    def add_posts(posts: List[Dict]) -> int:
        added = 0
        for post in posts or []:
            emails = [e.strip().lower() for e in post.get("emails", "").split(",") if e.strip()]
            new_emails = [e for e in emails if e not in seen_attempt_emails]

            if not new_emails:
                continue

            for e in new_emails:
                seen_attempt_emails.add(e)

            post["emails"] = ", ".join(new_emails)
            all_attempt_posts.append(post)
            added += 1

        return added

    for attempt, label in enumerate(labels):
        print(f"   Filter: {label}")

        if not driver_is_alive(driver):
            raise WebDriverException("Driver session is not alive")

        try:
            search_posts(driver, keyword, attempt=attempt)
            scroll_and_load_posts(driver)
            click_see_more_buttons(driver, limit=12)
        except Exception as e:
            logger.warning(f"Driver session lost or page load failed: {e}")
            raise

        try:
            screenshot_path = SCREENSHOTS_DIR / f"search_{keyword.replace(' ', '_')}_try{attempt + 1}.png"
            driver.save_screenshot(str(screenshot_path))
            logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception:
            pass

        post_elements = find_post_elements(driver)

        if page_has_no_results(driver) or len(post_elements) == 0:
            print(f"   ⚠️ No posts visible for {label}.")
            continue

        # 1) Fast mode: extract emails from currently loaded page text first.
        fast_posts = extract_page_level_leads(driver, keyword)
        fast_added = add_posts(fast_posts)
        if fast_posts:
            print(f"   ⚡ Fast page extraction added {len(fast_posts)} lead(s).")
            return fast_posts

        # 2) Deeper card-level extraction for remaining visible posts.
        posts = extract_post_data(driver, keyword)
        added = add_posts(posts)

        if added:
            print(f"   ✅ Card extraction added {added} lead(s) for {label}.")
        else:
            print(f"   ⚠️ No new email leads found for {label}. Trying next filter...")

        # Do NOT return after first lead. Keep trying fallback filters to collect more LinkedIn leads.

    return all_attempt_posts

def scrape_linkedin_posts(keywords: Optional[List[str]] = None) -> List[Dict]:
    if keywords is None:
        from config import DEFAULT_SEARCH_KEYWORDS
        keywords = DEFAULT_SEARCH_KEYWORDS

    all_posts = []
    global_seen_emails = set()
    driver = None

    try:
        driver = create_driver()

        if not wait_for_manual_login(driver):
            logger.error("LinkedIn login failed. Aborting scrape.")
            return []

        for keyword in keywords:
            print(f"\n🔍 Searching LinkedIn posts for: '{keyword}'")
            logger.info(f"Processing keyword: {keyword}")

            # If Chrome died after a previous keyword, restart and continue.
            if not driver_is_alive(driver):
                logger.warning("Driver is dead before keyword. Restarting Chrome...")
                driver = restart_driver(driver)

            try:
                posts = scrape_keyword_with_fallback(driver, keyword)
            except Exception as e:
                logger.warning(f"Keyword '{keyword}' failed due to browser/session issue: {e}")
                try:
                    print("   🔁 Restarting LinkedIn browser session and retrying keyword once...")
                    driver = restart_driver(driver)
                    posts = scrape_keyword_with_fallback(driver, keyword)
                except Exception as retry_error:
                    logger.error(f"Retry failed for keyword '{keyword}': {retry_error}")
                    posts = []

            unique_posts = []

            for post in posts:
                emails = [e.strip().lower() for e in post.get("emails", "").split(",") if e.strip()]
                new_emails = [e for e in emails if e not in global_seen_emails]

                if not new_emails:
                    continue

                for e in new_emails:
                    global_seen_emails.add(e)

                post["emails"] = ", ".join(new_emails)
                unique_posts.append(post)

            all_posts.extend(unique_posts)

            print(f"   ✅ Found {len(unique_posts)} unique posts with emails for '{keyword}'")
            _random_delay(1, 2)

    except Exception as e:
        logger.error(f"Scraping error: {e}")

    finally:
        if driver:
            print("\n🔒 Closing browser...")
            try:
                driver.quit()
            except Exception:
                pass

    logger.info(f"Total unique posts with emails found: {len(all_posts)}")
    return all_posts
