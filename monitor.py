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
                    """(el) => ({
                        src: el.currentSrc || el.src || "",
                        complete: !!el.complete,
                        naturalWidth: el.naturalWidth || 0,
                        naturalHeight: el.naturalHeight || 0
                    })"""
                )

                if not data["complete"] or data["naturalWidth"] == 0 or data["naturalHeight"] == 0:
                    problems.append(f"{i}. {data['src']}")
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


def main():
    problems = check_images()

    if problems:
        body = "Atrastas problēmas ar attēliem:\\n\\n" + "\\n".join(problems)
        send_email("Letonika: atrastas problēmas ar attēliem", body)
        print(body)
    else:
        print("Viss kārtībā. E-pasts netika sūtīts.")


if __name__ == "__main__":
    main()
