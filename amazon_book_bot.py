
import sys
sys.path.insert(0, "packages")

from playwright.sync_api import sync_playwright
# -------------------------
# USER PREFERENCES
# -------------------------

book_topic = "Python programming for beginners"
amazon_country = "www.amazon.com"

# -------------------------
# START THE BOT
# -------------------------

with sync_playwright() as p:

    # Open a visible browser
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    # Build the Amazon search URL
    search_url = (
        f"https://{amazon_country}/s?k="
        + book_topic.replace(" ", "+")
    )

    print("Opening Amazon...")
    page.goto(search_url, wait_until="domcontentloaded")

    # Allow time for the page to load results
    page.wait_for_timeout(5000)

    print("Amazon search page opened!")
    print("Search topic:", book_topic)

    # Find search result containers
    books = page.locator(
        '[data-component-type="s-search-result"]'
    )

    total_books = books.count()

    print(f"\nBooks found on page: {total_books}\n")

    # Read the first 10 results
    for i in range(min(total_books, 10)):

        book = books.nth(i)

        # Get book title
        title_element = book.locator("h2 span")

        if title_element.count() > 0:
            title = title_element.first.inner_text()
        else:
            title = "Title unavailable"

        # Get price
        price_element = book.locator(".a-price")

        if price_element.count() > 0:
            price = price_element.first.inner_text()
        else:
            price = "Price unavailable"

        # Get rating
        rating_element = book.locator(".a-icon-alt")

        if rating_element.count() > 0:
            rating = rating_element.first.inner_text()
        else:
            rating = "Rating unavailable"

        print(f"BOOK {i + 1}")
        print("Title:", title)
        print("Price:", price)
        print("Rating:", rating)
        print("-" * 40)

    # Keep the browser open until you close it
    input("\nPress ENTER to close the bot...")

    browser.close()
