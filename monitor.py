import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

URL = os.getenv("TARGET_URL", "https://letonika.lv")
EMAIL_TO = os.getenv("EMAIL_TO")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")


def check_images():
    problems = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 2000})
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(3000)

        images = page.locator("img").all()

        for i, img in enumerate(images, start=1):
            try:
                data = img.evaluate(
    """(el) => {
        const parentText = el.parentElement ? (el.parentElement.innerText || "") : "";
        const grandParentText = el.parentElement && el.parentElement.parentElement
            ? (el.parentElement.parentElement.innerText || "")
            : "";

        const clean = (txt) =>
            (txt || "")
                .replace(/\\s+/g, " ")
                .trim()
                .slice(0, 200);

        return {
            src: el.currentSrc || el.src || "",
            alt: el.alt || "",
            complete: !!el.complete,
            naturalWidth: el.naturalWidth || 0,
            naturalHeight: el.naturalHeight || 0,
            parentText: clean(parentText),
            grandParentText: clean(grandParentText)
        };
    }"""
)

                if not data["complete"] or data["naturalWidth"] == 0 or data["naturalHeight"] == 0:
                    problems.append(f"{i}. {safe_text_url(data['src'])}")
            except Exception as e:
                problems.append(f"{i}. Kļūda, pārbaudot attēlu: {e}")

        browser.close()

    return problems


def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

def safe_text_url(url):
    return url.replace("https://", "https[:]//").replace("http://", "http[:]//")

def main():
    problems = check_images()

    if problems:
        subject = "Letonika: problēmas ar attēliem"

        body = (
            f"Statuss: ATRASTAS PROBLĒMAS\n"
            f"Lapa: {safe_text_url(URL)}\n"
            f"Problēmu skaits: {len(problems)}\n\n"
            "Bojātie attēli:\n"
            "----------------------------------\n"
            + "\n".join(problems)
            + "\n\nRīcība: pārbaudi attēlus lapā."
        )

        send_email(subject, body)
        print(body)

    else:
        subject = "Letonika: visi attēli redzami"

        body = (
            f"Statuss: VISS KĀRTĪBĀ\n"
            f"Lapa: {safe_text_url(URL)}\n"
            "Visi attēli ielādējas korekti.\n"
            "Nav konstatētas problēmas."
        )

        send_email(subject, body)
        print(body)


if __name__ == "__main__":
    main()
