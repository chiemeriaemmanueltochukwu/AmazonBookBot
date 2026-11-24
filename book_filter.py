
import csv
import re

print("======================================")
print("       AMAZON BOOK FILTER SYSTEM")
print("======================================")

# USER REQUIREMENTS

topic = input("Enter desired book topic: ")

max_price = float(input("Enter maximum price in USD: "))

min_rating = float(input("Enter minimum rating (e.g. 4.0): "))

preferred_author = input(
    "Enter preferred author (or press Enter for any): "
).strip().lower()

# Convert price into a number
def extract_price(price_text):
    try:
        match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", price_text)

        if match:
            return float(match.group().replace(",", ""))

    except (ValueError, TypeError):
        pass

    return None


# Convert rating into a number
def extract_rating(rating_text):
    try:
        match = re.search(r"\d+(?:\.\d+)?", rating_text)

        if match:
            return float(match.group())

    except (ValueError, TypeError):
        pass

    return None


matching_books = []

print("\nReading Amazon book records...")

try:

    with open(
        "amazon_books.csv",
        "r",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for book in reader:

            title = book.get("Title", "").strip()

            price_text = book.get("Price", "")

            rating_text = book.get("Rating", "")

            price = extract_price(price_text)

            rating = extract_rating(rating_text)

            # Check whether information is available
            if price is None or rating is None:
                continue

            # Check price
            if price > max_price:
                continue

            # Check rating
            if rating < min_rating:
                continue

            # Check author if specified
            if preferred_author:

                book_details = (
                    title + " " +
                    book.get("Author", "")
                ).lower()

                if preferred_author not in book_details:
                    continue

            matching_books.append(book)

    # Rank by rating, then price
    matching_books.sort(
        key=lambda b: (
            -extract_rating(b["Rating"]),
            extract_price(b["Price"])
        )
    )

    # Save matching books
    with open(
        "filtered_books.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        if matching_books:

            writer = csv.DictWriter(
                file,
                fieldnames=matching_books[0].keys()
            )

            writer.writeheader()
            writer.writerows(matching_books)

    print("\n======================================")
    print("FILTERING COMPLETED")
    print("======================================")

    print("Matching books:", len(matching_books))

    for number, book in enumerate(matching_books, 1):

        print(f"\nBOOK {number}")
        print("Title:", book["Title"])
        print("Price:", book["Price"])
        print("Rating:", book["Rating"])

    if not matching_books:
        print("\nNo books matched your specifications.")

    print("\nResults saved to filtered_books.csv")

except FileNotFoundError:

    print("\nERROR: amazon_books.csv was not found.")

    print("Run amazon_search.py first.")

except ValueError:

    print("\nERROR: Please enter valid numerical values.")

print("\nFiltering system finished!")
