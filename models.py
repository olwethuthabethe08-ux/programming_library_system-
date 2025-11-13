from sqlalchemy import create_engine, Column, Integer, String, Text, Date, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# --- 1. Database Setup (SQLite for simplicity, but easily changeable to PostgreSQL) ---
DATABASE_URL = "sqlite:///lms_database.db"
engine = create_engine(DATABASE_URL)

Base = declarative_base()
from datetime import datetime, timedelta
from lms_api_service import send_sms_notification, send_email_notification

# --- 1. Database Setup (SQLite for simplicity, but easily changeable to PostgreSQL) ---
DATABASE_URL = "sqlite:///lms_database.db"
engine = create_engine(DATABASE_URL)

# Base is defined above for SQLAlchemy 1.4 compatibility

# --- 2. Database Models (Based on Project 2 Requirements) ---

class Book(Base):
    __tablename__ = "books"
    
    # Primary Key
    book_id = Column(Integer, primary_key=True, index=True)
    
    # Core Book Details
    isbn = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String)
    publisher = Column(String)
    publication_year = Column(Integer)
    category = Column(String)
    description = Column(Text)
    cover_image_url = Column(String)
    
    # Inventory Details
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    shelf_location = Column(String)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="book")
    reviews = relationship("BookReview", back_populates="book")

    def __repr__(self):
        return f"<Book(title='{self.title}', isbn='{self.isbn}')>"

class Member(Base):
    __tablename__ = "members"
    
    # Primary Key
    member_id = Column(Integer, primary_key=True, index=True)
    
    # Member Details
    membership_number = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True)
    phone = Column(String)
    join_date = Column(Date, default=datetime.now().date())
    membership_type = Column(String, default="Standard")
    status = Column(String, default="Active") # e.g., Active, Suspended
    
    # Relationships
    transactions = relationship("Transaction", back_populates="member")
    reviews = relationship("BookReview", back_populates="member")

    def __repr__(self):
        return f"<Member(name='{self.first_name} {self.last_name}', number='{self.membership_number}')>"

class Transaction(Base):
    __tablename__ = "transactions"
    
    # Primary Key
    transaction_id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    member_id = Column(Integer, ForeignKey("members.member_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)
    
    # Transaction Details
    issue_date = Column(Date, default=datetime.now().date())
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    fine_amount = Column(Float, default=0.0)
    status = Column(String, default="Issued") # e.g., Issued, Returned, Overdue
    
    # Relationships
    member = relationship("Member", back_populates="transactions")
    book = relationship("Book", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, status='{self.status}')>"

class BookReview(Base):
    __tablename__ = "book_reviews"
    
    # Primary Key
    review_id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.member_id"), nullable=False)
    
    # Review Details
    rating = Column(Integer) # e.g., 1 to 5
    review_text = Column(Text)
    review_date = Column(Date, default=datetime.now().date())
    
    # Relationships
    book = relationship("Book", back_populates="reviews")
    member = relationship("Member", back_populates="reviews")

    def __repr__(self):
        return f"<Review(book_id={self.book_id}, rating={self.rating})>"

# --- 3. Initialization and Session Management ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def initialize_database():
    """Creates the database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. Core Business Logic Functions ---

def get_dashboard_stats(db_session):
    """Retrieves key statistics for the dashboard."""
    total_books = db_session.query(Book).count()
    total_members = db_session.query(Member).count()
    books_on_loan = db_session.query(Transaction).filter(Transaction.status == "Issued").count()
    
    return {
        "total_books": total_books,
        "total_members": total_members,
        "books_on_loan": books_on_loan
    }

def get_all_books(db_session):
    """Retrieves all books from the database."""
    return db_session.query(Book).all()

def get_all_members(db_session):
    """Retrieves all members from the database."""
    return db_session.query(Member).all()

def get_transactions_needing_reminder(db_session, days_before_due: int = 3):
    """Retrieves transactions due in the next 'days_before_due' days."""
    today = datetime.now().date()
    reminder_date = today + timedelta(days=days_before_due)
    
    reminder_transactions = db_session.query(Transaction).filter(
        Transaction.status == "Issued",
        Transaction.due_date == reminder_date
    ).all()
    
    return reminder_transactions

def send_due_date_reminders(db_session):
    """
    Sends reminders for books due in 3 days and for all overdue books.
    Returns a summary of actions taken.
    """
    summary = {"reminders_sent": 0, "overdue_alerts_sent": 0}
    
    # --- 1. Send Reminders for Books Due in 3 Days ---
    reminders = get_transactions_needing_reminder(db_session, days_before_due=3)
    for trans in reminders:
        member = trans.member
        book = trans.book
        
        subject = f"Reminder: Your book '{book.title}' is due soon!"
        email_content = f"Dear {member.first_name},\n\nThis is a reminder that the book '{book.title}' is due on {trans.due_date.strftime('%Y-%m-%d')}. Please return it to avoid fines.\n\nThank you,\nLibrary Management System"
        sms_content = f"REMINDER: '{book.title}' due {trans.due_date.strftime('%m/%d')}. Return to avoid fines."
        
        if send_email_notification(member.email, subject, email_content):
            summary["reminders_sent"] += 1
        if send_sms_notification(member.phone, sms_content):
            # Assuming phone number is valid
            pass

    # --- 2. Send Alerts for Overdue Books ---
    overdue_list = get_overdue_transactions(db_session)
    for item in overdue_list:
        # Re-fetch transaction object to get member/book details
        trans = db_session.query(Transaction).filter(Transaction.transaction_id == item["transaction_id"]).first()
        member = trans.member
        
        subject = f"URGENT: Your book '{item['book_title']}' is overdue!"
        email_content = f"Dear {member.first_name},\n\nThe book '{item['book_title']}' was due on {item['due_date']} and is now {item['overdue_days']} days overdue. Please return it immediately. A fine of ${item['overdue_days'] * 0.50:.2f} has been assessed.\n\nLibrary Management System"
        sms_content = f"OVERDUE: '{item['book_title']}' is {item['overdue_days']} days overdue. Fine assessed."
        
        if send_email_notification(member.email, subject, email_content):
            summary["overdue_alerts_sent"] += 1
        if send_sms_notification(member.phone, sms_content):
            # Assuming phone number is valid
            pass
            
    return summary

def get_overdue_transactions(db_session):
    """Retrieves a list of all currently overdue transactions."""
    today = datetime.now().date()
    overdue_transactions = db_session.query(Transaction).filter(
        Transaction.status == "Issued",
        Transaction.due_date < today
    ).all()
    
    report_data = []
    for trans in overdue_transactions:
        overdue_days = (today - trans.due_date).days
        report_data.append({
            "transaction_id": trans.transaction_id,
            "book_title": trans.book.title,
            "member_name": f"{trans.member.first_name} {trans.member.last_name}",
            "due_date": trans.due_date.strftime("%Y-%m-%d"),
            "overdue_days": overdue_days
        })
        
    return report_data

def add_book_to_db(db_session, book_data: dict):
    """Adds a new book to the database from API lookup data."""
    # Ensure ISBN is unique before adding
    existing_book = db_session.query(Book).filter(Book.isbn == book_data["isbn"]).first()
    if existing_book:
        # If book exists, just increment total/available copies
        existing_book.total_copies += 1
        existing_book.available_copies += 1
        db_session.commit()
        return existing_book

    new_book = Book(
        isbn=book_data["isbn"],
        title=book_data["title"],
        author=book_data["author"],
        publisher=book_data["publisher"],
        publication_year=book_data["publication_year"],
        category=book_data["category"],
        description=book_data["description"],
        cover_image_url=book_data["cover_image_url"],
        total_copies=1,
        available_copies=1,
        shelf_location="A1" # Placeholder
    )
    db_session.add(new_book)
    db_session.commit()
    db_session.refresh(new_book)
    return new_book

def issue_book(db_session, member_id: int, book_id: int, loan_days: int = 14):
    """Issues a book to a member, creating a transaction and updating inventory."""
    book = db_session.query(Book).filter(Book.book_id == book_id).first()
    member = db_session.query(Member).filter(Member.member_id == member_id).first()

    if not book:
        return {"success": False, "message": "Book not found."}
    if not member:
        return {"success": False, "message": "Member not found."}
    if book.available_copies <= 0:
        return {"success": False, "message": f"Book '{book.title}' is currently out of stock."}

    # 1. Update Book Inventory
    book.available_copies -= 1
    
    # 2. Create Transaction
    due_date = datetime.now().date() + timedelta(days=loan_days)
    new_transaction = Transaction(
        member_id=member_id,
        book_id=book_id,
        due_date=due_date,
        status="Issued"
    )
    db_session.add(new_transaction)
    
    # 3. Commit changes
    db_session.commit()
    db_session.refresh(new_transaction)
    
    return {"success": True, "message": f"Book '{book.title}' issued to {member.first_name} {member.last_name}. Due date: {due_date}"}

def return_book(db_session, transaction_id: int, fine_rate: float = 0.50):
    """Handles the return of a book, calculates fines, and updates inventory."""
    transaction = db_session.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()

    if not transaction:
        return {"success": False, "message": "Transaction not found."}
    if transaction.status == "Returned":
        return {"success": False, "message": "Book already returned."}

    # 1. Calculate Fine
    return_date = datetime.now().date()
    overdue_days = max(0, (return_date - transaction.due_date).days)
    fine_amount = overdue_days * fine_rate
    
    # 2. Update Transaction
    transaction.return_date = return_date
    transaction.fine_amount = fine_amount
    transaction.status = "Returned"
    
    # 3. Update Book Inventory
    book = db_session.query(Book).filter(Book.book_id == transaction.book_id).first()
    if book:
        book.available_copies += 1
    
    # 4. Commit changes
    db_session.commit()
    
    message = f"Book returned successfully. Overdue days: {overdue_days}. Fine amount: ${fine_amount:.2f}"
    return {"success": True, "message": message, "fine_amount": fine_amount}

# Example usage:
if __name__ == "__main__":
    initialize_database()
    
    # Add a dummy member for testing
    db = SessionLocal()
    if not db.query(Member).first():
        dummy_member = Member(membership_number="M001", first_name="Alice", last_name="Smith", email="alice@example.com", phone="555-1234")
        db.add(dummy_member)
        db.commit()
        db.refresh(dummy_member)
        print(f"Added dummy member: {dummy_member}")
    db.close()
