import csv
import re
import time
from urllib.parse import quote_plus
from pathlib import Path

from playwright.sync_api import sync_playwright

OUTPUT = Path(__file__).with_name("amazon_books.csv")
MAX_PAGES = 3


def ask_specs():
    print("\n--- Optional book specifications (leave blank to accept any) ---")
    return {
        "max_price": input("Maximum price (number, e.g. 25; blank = any): ").strip(),
        "min_rating": input("Minimum rating (0-5; blank = any): ").strip(),
        "min_reviews": input("Minimum review count (number; blank = any): ").strip(),
        "author": input("Preferred author (blank = any): ").strip().lower(),
        "format": input("Format (Kindle, Paperback, Hardcover, etc.; blank = any): ").strip().lower(),
    }


def get_price(text):
    match = re.search(r"\$\s*(\d+(?:\.\d{1,2})?)", text)
    return float(match.group(1)) if match else None


def get_rating(text):
    match = re.search(r"(\d(?:\.\d)?)\s+out of 5 stars", text, re.I)
    return float(match.group(1)) if match else None


def get_reviews(text):
    match = re.search(r"([\d,]+)\s+(?:ratings|reviews)", text, re.I)
    return int(match.group(1).replace(",", "")) if match else None


def matches(text, title, specs):
    price = get_price(text)
    rating = get_rating(text)
    reviews = get_reviews(text)

    if specs["max_price"]:
        try:
            limit = float(specs["max_price"])
        except ValueError:
            print("Invalid maximum price entered; ignoring that filter.")
            limit = None
        if limit is not None and (price is None or price > limit):
            return False

    if specs["min_rating"]:
        try:
            min_rating = float(specs["min_rating"])
        except ValueError:
            print("Invalid minimum rating entered; ignoring that filter.")
            min_rating = None
        if min_rating is not None and (rating is None or rating < min_rating):
            return False

    if specs["min_reviews"]:
        try:
            min_reviews = int(specs["min_reviews"])
        except ValueError:
            print("Invalid minimum review count entered; ignoring that filter.")
            min_reviews = None
        if min_reviews is not None and (reviews is None or reviews < min_reviews):
            return False

    if specs["author"] and specs["author"] not in text.lower():
        return False
    if specs["format"] and specs["format"] not in text.lower():
        return False
    return True


def main():
    print("=== Amazon Book Search Bot ===")
    print("1. General search (no filters)")
    print("2. Search with optional specifications")
    mode = input("Choose 1 or 2: ").strip()
    topic = input("Book topic/title (blank defaults to books): ").strip() or "books"
    specs = {"max_price": "", "min_rating": "", "min_reviews": "", "author": "", "format": ""}
    if mode == "2":
        specs = ask_specs()
    elif mode != "1":
        print("Invalid option. Please run again and choose 1 or 2.")
        return

    collected = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            for page_number in range(1, MAX_PAGES + 1):
                search_url = f"https://www.amazon.com/s?k={quote_plus(topic)}&i=stripbooks&page={page_number}"
                print(f"\nOpening search page {page_number}: {topic}")
                page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3500)

                # If Amazon displays a CAPTCHA or access challenge, stop and let the user handle it manually.
                challenge = page.locator("input[name='captchacharacters'], #captchacharacters").count()
                if challenge:
                    print("Amazon is showing a verification challenge. Please handle it manually in the browser; the bot will stop.")
                    break

                cards = page.locator("div[data-component-type='s-search-result']")
                count = cards.count()
                print(f"Found {count} result cards on this page.")

                for i in range(count):
                    card = cards.nth(i)
                    try:
                        title_el = card.locator("h2 a span").first
                        title = title_el.inner_text(timeout=3000).strip()
                        link = card.locator("h2 a").first.get_attribute("href")
                        if not title or not link:
                            continue
                        full_link = link if link.startswith("http") else "https://www.amazon.com" + link
                        if full_link in seen:
                            continue
                        text = card.inner_text(timeout=3000)
                        if mode == "2" and not matches(text, title, specs):
                            continue
                        seen.add(full_link)
                        collected.append({
                            "Title": title,
                            "Author_or_details": text.replace("\n", " | ")[:500],
                            "Price_USD": get_price(text),
                            "Rating": get_rating(text),
                            "Reviews": get_reviews(text),
                            "Link": full_link,
                        })
                    except Exception as exc:
                        print(f"Skipping a result due to a reading error: {exc}")

                if page_number < MAX_PAGES:
                    time.sleep(2.5)

        except Exception as exc:
            print(f"Search stopped because of an error: {exc}")
        finally:
            browser.close()

    if collected:
        with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=collected[0].keys())
            writer.writeheader()
            writer.writerows(collected)
        print(f"\nSaved {len(collected)} book results to: {OUTPUT}")
    else:
        print("\nNo books were collected. Amazon may have changed its page layout, or the search returned no accessible results.")
    print("Amazon Book Bot finished.")


if __name__ == "__main__":
    main()
