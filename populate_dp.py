import requests
import json
from sqlalchemy.orm import sessionmaker
from lms_models import initialize_database, engine, Book, add_book_to_db, Member
from lms_api_service import GOOGLE_BOOKS_API_URL

# Setup Database Session
initialize_database()
Session = sessionmaker(bind=engine)
db_session = Session()

def fetch_book_details(isbn: str) -> dict:
    """
    Fetches book details from the Google Books API for a given ISBN.
    This is a slightly more robust version of the placeholder in lms_api_service.
    """
    try:
        params = {"q": f"isbn:{isbn}"}
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("totalItems", 0) > 0:
            item = data["items"][0]["volumeInfo"]
            
            # Extract image link, prioritizing the largest available thumbnail
            image_links = item.get("imageLinks", {})
            cover_image_url = image_links.get("extraLarge") or \
                              image_links.get("large") or \
                              image_links.get("medium") or \
                              image_links.get("small") or \
                              image_links.get("thumbnail")
            
            book_details = {
                "isbn": isbn,
                "title": item.get("title", "N/A"),
                "author": ", ".join(item.get("authors", ["N/A"])),
                "publisher": item.get("publisher", "N/A"),
                "publication_year": int(item.get("publishedDate", "0000")[:4]),
                "category": ", ".join(item.get("categories", ["General"])),
                "description": item.get("description", "No description available."),
                "cover_image_url": cover_image_url,
                "success": True
            }
            return book_details
        else:
            return {"success": False, "message": f"No book found for ISBN: {isbn}"}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"API Request Failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"An unexpected error occurred: {e}"}

def populate_books_from_list(isbn_file_path: str):
    """Reads ISBNs from a file and populates the database."""
    print("--- Starting Database Population ---")
    
    with open(isbn_file_path, 'r') as f:
        isbns = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    for i, isbn in enumerate(isbns):
        print(f"[{i+1}/{len(isbns)}] Processing ISBN: {isbn}...")
        
        # Check if book already exists to avoid unnecessary API calls
        if db_session.query(Book).filter(Book.isbn == isbn).first():
            print(f"Book with ISBN {isbn} already exists. Skipping API call.")
            continue

        book_data = fetch_book_details(isbn)
        
        if book_data["success"]:
            try:
                # Add book to DB (add_book_to_db handles the commit)
                new_book = add_book_to_db(db_session, book_data)
                print(f"  SUCCESS: Added/Updated book: {new_book.title}")
            except Exception as e:
                print(f"  DB ERROR: Could not add book {isbn}. Error: {e}")
                db_session.rollback()
        else:
            print(f"  FAILURE: {book_data['message']}")

    print("--- Database Population Complete ---")

def ensure_dummy_member():
    """Ensures a dummy member exists for testing transactions."""
    if not db_session.query(Member).filter(Member.membership_number == "M001").first():
        dummy_member = Member(membership_number="M001", first_name="Alice", last_name="Smith", email="alice@example.com", phone="555-1234")
        db_session.add(dummy_member)
        db_session.commit()
        print("Ensured dummy member (Alice Smith) exists.")

if __name__ == "__main__":
    ensure_dummy_member()
    populate_books_from_list("isbn_list.txt")
    db_session.close()
