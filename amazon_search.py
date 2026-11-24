import sys
import os
import csv
import re

# Tell Python where Playwright is installed
project_folder = os.path.dirname(os.path.abspath(__file__))
packages_folder = os.path.join(project_folder, "packages")

sys.path.insert(0, packages_folder)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
import csv
import os
import re


print("====================================")
print("       AMAZON BOOK READER BOT")
print("====================================")

# ====================================
# SEARCH MODE
# ====================================

print("\nHow would you like to search?")
print("1. General book search (any kind)")
print("2. Search using specifications")

search_mode = input("\nEnter your choice (1 or 2): ").strip()

while search_mode not in ("1", "2"):
    print("Invalid choice. Please enter 1 or 2.")
    search_mode = input("Enter your choice: ").strip()


# ====================================
# BOOK SEARCH INPUT
# ====================================

topic = input(
    "\nEnter book topic (press ENTER for any book): "
).strip()

if not topic:
    topic = "books"


# ====================================
# SPECIFICATIONS
# ====================================

max_price = None
min_rating = None
min_reviews = None
preferred_author = ""
preferred_format = ""

if search_mode == "2":

    print("\n====================================")
    print("       BOOK SPECIFICATIONS")
    print("====================================")

    max_price_input = input(
        "Maximum price (ENTER for no limit): "
    ).strip()

    min_rating_input = input(
        "Minimum rating (ENTER for no limit): "
    ).strip()

    min_reviews_input = input(
        "Minimum reviews (ENTER for no limit): "
    ).strip()

    preferred_author = input(
        "Preferred author (ENTER for any author): "
    ).strip()

    preferred_format = input(
        "Preferred format (ENTER for any format): "
    ).strip()

    # Convert price to a number
    if max_price_input:
        try:
            max_price = float(max_price_input)

            if max_price < 0:
                print("Price cannot be negative.")
                max_price = None

        except ValueError:
            print("Invalid price. No maximum price will be applied.")
            max_price = None

    # Convert rating to a number
    if min_rating_input:
        try:
            min_rating = float(min_rating_input)

            if min_rating < 0 or min_rating > 5:
                print("Rating must be between 0 and 5.")
                min_rating = None

        except ValueError:
            print("Invalid rating. No rating filter will be applied.")
            min_rating = None

    # Convert reviews to an integer
    if min_reviews_input:
        try:
            min_reviews = int(min_reviews_input)

            if min_reviews < 0:
                print("Review count cannot be negative.")
                min_reviews = None

        except ValueError:
            print("Invalid review count. No review filter will be applied.")
            min_reviews = None


# ====================================
# SEARCH SETTINGS
# ====================================

book_list = []
seen_links = set()

# Maximum Amazon pages to search
max_pages = 5

# Save CSV files beside this Python file
project_folder = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(
    project_folder,
    "amazon_books.csv"
)

filtered_csv_path = os.path.join(
    project_folder,
    "filtered_books.csv"
)


# ====================================
# HELPER FUNCTION: EXTRACT TEXT
# ====================================

def get_text(element, selector):

    try:
        item = element.locator(selector).first

        if item.count() > 0:
            return item.inner_text().strip()

    except Exception:
        pass

    return "Not available"


# ====================================
# HELPER FUNCTION: EXTRACT PRICE
# ====================================

def extract_price(price_text):

    if not price_text or price_text == "Not available":
        return None

    # Find a numerical price
    match = re.search(
        r"(\d[\d,]*\.?\d*)",
        price_text
    )

    if match:
        try:
            return float(match.group(1).replace(",", ""))

        except ValueError:
            return None

    return None


# ====================================
# HELPER FUNCTION: EXTRACT RATING
# ====================================

def extract_rating(rating_text):

    if not rating_text or rating_text == "Not available":
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*out of 5",
        rating_text,
        re.IGNORECASE
    )

    if match:
        try:
            return float(match.group(1))

        except ValueError:
            return None

    return None


# ====================================
# HELPER FUNCTION: EXTRACT REVIEWS
# ====================================

def extract_reviews(review_text):

    if not review_text or review_text == "Not available":
        return None

    # Remove commas before converting to integer
    numbers = re.findall(
        r"\d[\d,]*",
        review_text
    )

    if numbers:
        try:
            return int(numbers[0].replace(",", ""))

        except ValueError:
            return None

    return None


# ====================================
# HELPER FUNCTION: DETECT FORMAT
# ====================================

def detect_format(book_text):

    text = book_text.lower()

    formats = [
        "kindle",
        "paperback",
        "hardcover",
        "spiral-bound",
        "audio book",
        "audiobook",
        "mass market paperback",
        "board book"
    ]

    detected_formats = []

    for book_format in formats:

        if book_format in text:
            detected_formats.append(book_format.title())

    if detected_formats:
        return ", ".join(dict.fromkeys(detected_formats))

    return "Not available"


# ====================================
# HELPER FUNCTION: FILTER BOOKS
# ====================================

def matches_specifications(book):

    # General search: no filters
    if search_mode == "1":
        return True

    # -------------------------------
    # PRICE FILTER
    # -------------------------------

    if max_price is not None:

        price = extract_price(book["Price"])

        # Cannot verify price, so reject it
        if price is None:
            return False

        if price > max_price:
            return False

    # -------------------------------
    # RATING FILTER
    # -------------------------------

    if min_rating is not None:

        rating = extract_rating(book["Rating"])

        if rating is None:
            return False

        if rating < min_rating:
            return False

    # -------------------------------
    # REVIEW FILTER
    # -------------------------------

    if min_reviews is not None:

        reviews = extract_reviews(book["Reviews"])

        if reviews is None:
            return False

        if reviews < min_reviews:
            return False

    # -------------------------------
    # AUTHOR FILTER
    # -------------------------------

    if preferred_author:

        author = book["Author"].lower()

        if preferred_author.lower() not in author:
            return False

    # -------------------------------
    # FORMAT FILTER
    # -------------------------------

    if preferred_format:

        book_format = book["Format"].lower()

        if preferred_format.lower() not in book_format:
            return False

    # Passed every supplied specification
    return True


# ====================================
# GET MATCHING BOOKS
# ====================================

def get_matching_books():

    matching_books = []

    for book in book_list:

        if matches_specifications(book):
            matching_books.append(book)

    return matching_books


# ====================================
# SAVE BOOKS TO CSV
# ====================================

def save_books():

    print("\nSaving book results...")

    try:

        if search_mode == "1":
            books_to_save = book_list

        else:
            books_to_save = get_matching_books()

        with open(
            csv_path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            columns = [
                "Title",
                "Author",
                "Price",
                "Rating",
                "Reviews",
                "Format",
                "Link"
            ]

            writer = csv.DictWriter(
                file,
                fieldnames=columns
            )

            writer.writeheader()
            writer.writerows(books_to_save)

        print("\nCSV SUCCESSFULLY SAVED!")
        print("Location:", csv_path)
        print("Books saved:", len(books_to_save))

    except Exception as error:

        print("CSV saving error:", error)


# ====================================
# START BOT
# ====================================

browser = None

try:

    # Check whether Playwright is installed
    if sync_playwright is None:

        print("\nPlaywright is not installed.")
        print("Install it using:")
        print("python -m pip install playwright")
        raise SystemExit

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        print("\nOpening Amazon...")

        page.goto(
            "https://www.amazon.com/",
            wait_until="domcontentloaded",
            timeout=60000
        )

        # ====================================
        # SEARCH FOR BOOKS
        # ====================================

        search_box = page.locator(
            "#twotabsearchtextbox"
        )

        search_box.wait_for(timeout=20000)

        search_box.fill(topic)

        page.locator(
            "#nav-search-submit-button"
        ).click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(4000)

        # ====================================
        # AMAZON PAGE DIAGNOSTICS
        # ====================================

        print("\n===== AMAZON PAGE DIAGNOSTICS =====")

        print("Current URL:", page.url)
        print("Page title:", page.title())

        try:
            page_text = page.locator("body").inner_text()
            print("\nPAGE CONTENT:")
            print(page_text[:2500])
        except Exception as error:
            print("Could not read page content:", error)

        # Save a screenshot for inspection
        screenshot_path = os.path.join(
            project_folder,
            "amazon_debug.png"
        )

        page.screenshot(
            path=screenshot_path,
            full_page=True
        )

        print("\nScreenshot saved:", screenshot_path)

        pages_visited = 0

        # ====================================
        # MULTI-PAGE COLLECTION
        # ====================================

        for page_number in range(1, max_pages + 1):

            print("\n====================================")
            print(f"READING AMAZON PAGE {page_number}")
            print("====================================")

            books = page.locator(
                '[data-component-type="s-search-result"]'
            )

            total = books.count()

            print("Listings found:", total)

            if total == 0:

                print("No results found. Stopping.")
                break

            pages_visited += 1

            # ====================================
            # COLLECT BOOK INFORMATION
            # ====================================

            for i in range(min(total, 20)):

                book = books.nth(i)

                title = get_text(book, "h2")

                price = get_text(
                    book,
                    ".a-price .a-offscreen"
                )

                rating = get_text(
                    book,
                    ".a-icon-alt"
                )

                reviews = get_text(
                    book,
                    "a.s-underline-text span"
                )

                author = get_text(
                    book,
                    ".a-row.a-size-base.a-color-secondary"
                )

                # Get complete listing text
                try:
                    complete_text = book.inner_text()

                except Exception:
                    complete_text = ""

                book_format = detect_format(
                    complete_text
                )

                # ====================================
                # GET BOOK LINK
                # ====================================

                try:

                    link = book.locator(
                        "h2 a"
                    ).first.get_attribute("href")

                    if link and link.startswith("/"):

                        link = (
                            "https://www.amazon.com" + link
                        )

                    elif not link:

                        link = "Not available"

                except Exception:

                    link = "Not available"

                # ====================================
                # REMOVE DUPLICATES
                # ====================================

                if link == "Not available":

                    unique_key = title + author

                else:

                    unique_key = link

                if unique_key in seen_links:
                    continue

                seen_links.add(unique_key)

                # ====================================
                # STORE BOOK INFORMATION
                # ====================================

                book_info = {
                    "Title": title,
                    "Author": author,
                    "Price": price,
                    "Rating": rating,
                    "Reviews": reviews,
                    "Format": book_format,
                    "Link": link
                }

                book_list.append(book_info)

                print("\nBOOK", len(book_list))
                print("Title:", title)
                print("Author:", author)
                print("Price:", price)
                print("Rating:", rating)
                print("Reviews:", reviews)
                print("Format:", book_format)

            # ====================================
            # DISPLAY RESULTS SO FAR
            # ====================================

            print(
                "\nTotal unique books collected:",
                len(book_list)
            )

            if search_mode == "1":

                print(
                    "General search: no specifications applied."
                )

            else:

                matching_count = len(
                    get_matching_books()
                )

                print(
                    "Books currently matching specifications:",
                    matching_count
                )

            # ====================================
            # SAVE PROGRESS AFTER EVERY PAGE
            # ====================================

            save_books()

            # ====================================
            # PAGINATION
            # ====================================

            if page_number == max_pages:

                print("\nMaximum page limit reached.")
                break

            print("\n===== PAGINATION DIAGNOSTICS =====")

            print("Current URL:", page.url)

            next_button = page.locator(
                "a.s-pagination-next"
            )

            print(
                "Next button count:",
                next_button.count()
            )

            if next_button.count() == 0:

                print("Next button not found.")
                break

            next_button = next_button.first

            if not next_button.is_visible():

                print("Next button is not visible.")
                break

            button_class = (
                next_button.get_attribute("class") or ""
            )

            print("Next button class:", button_class)

            if "s-pagination-disabled" in button_class:

                print("Reached the last page.")
                break

            next_url = next_button.get_attribute("href")

            print("Next page destination:", next_url)

            if not next_url:

                print("Next page URL unavailable.")
                break

            if next_url.startswith("/"):

                next_url = (
                    "https://www.amazon.com" + next_url
                )

            old_url = page.url

            print("\nOpening next page...")

            try:

                page.goto(
                    next_url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                page.wait_for_timeout(4000)

                print("New URL:", page.url)

                if page.url == old_url:

                    print("URL did not change. Stopping.")
                    break

            except Exception as error:

                print("Navigation error:", error)
                break

        # ====================================
        # SEARCH COMPLETED
        # ====================================

        print("\n====================================")
        print("SEARCH COMPLETED!")
        print("====================================")

        print("Search topic:", topic)
        print("Pages visited:", pages_visited)
        print("Unique books collected:", len(book_list))

        if search_mode == "1":

            print("Search mode: General search")

            final_books = book_list

        else:

            print("Search mode: Specification-based")

            final_books = get_matching_books()

            print(
                "Books matching specifications:",
                len(final_books)
            )

            print(
                "Books rejected by filters:",
                len(book_list) - len(final_books)
            )

        # ====================================
        # DISPLAY FINAL MATCHES
        # ====================================

        print("\n====================================")
        print("       FINAL BOOK RESULTS")
        print("====================================")

        for number, book in enumerate(
            final_books,
            start=1
        ):

            print(f"\nBOOK {number}")
            print("Title:", book["Title"])
            print("Author:", book["Author"])
            print("Price:", book["Price"])
            print("Rating:", book["Rating"])
            print("Reviews:", book["Reviews"])
            print("Format:", book["Format"])
            print("Link:", book["Link"])

        print("\nFinal books saved to CSV.")

except Exception as error:

    print("\nPROGRAM ERROR:", error)

finally:

    # ====================================
    # ALWAYS ATTEMPT TO SAVE RESULTS
    # ====================================

    save_books()

    if browser is not None:

        try:
            browser.close()

        except Exception:
            pass

    print("\nAmazon Book Bot finished.")
