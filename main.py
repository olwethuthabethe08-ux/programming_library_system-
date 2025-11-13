import tkinter as tk
from tkinter import Menu, Frame, Label, Button, messagebox, ttk
from lms_api_service import lookup_book_by_isbn # Import the API service
from PIL import Image, ImageTk
import io
import requests
from lms_models import initialize_database, SessionLocal, add_book_to_db, issue_book, return_book, Member, Book # Import DB functions and models

# --- Design Constants ---
PRIMARY_COLOR = "#007bff"  # Blue
SECONDARY_COLOR = "#6c757d" # Gray
SUCCESS_COLOR = "#28a745"  # Green
DANGER_COLOR = "#dc3545"   # Red
FONT_FAMILY = "Arial"

class LMSApp:
    def __init__(self, master):
        # Initialize Database
        initialize_database()
        self.db_session = SessionLocal() # Keep a session open for simplicity in this example
        
        self.master = master
        master.title("Library Management System")
        master.geometry("1024x768")

        # Configure styles for a modern look
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", font=(FONT_FAMILY, 10, 'bold'))
        self.style.configure("TButton", font=(FONT_FAMILY, 10), padding=6)
        self.style.configure("Header.TLabel", font=(FONT_FAMILY, 18, 'bold'), foreground=PRIMARY_COLOR)
        self.style.configure("Status.TLabel", font=(FONT_FAMILY, 9), background="#f8f9fa")

        # 1. Menu Bar
        self.create_menu_bar()

        # 2. Toolbar Frame
        self.create_toolbar()

        # 3. Main Content Area (Using Notebook for sections)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.create_dashboard_tab()
        self.create_book_management_tab()
        self.create_member_management_tab()
        self.create_transaction_management_tab()

        # 4. Status Bar
        self.create_status_bar()
        self.update_status_simulated()
        
        # Initial data load for testing
        self.load_initial_data()

    # --- Menu Bar Implementation ---
    def create_menu_bar(self):
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        # File Menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Transaction", command=lambda: self.notebook.select(3))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)

        # Book Menu
        book_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Books", menu=book_menu)
        book_menu.add_command(label="Add New Book (with ISBN Lookup)", command=lambda: self.notebook.select(1))
        book_menu.add_command(label="Manage Books", command=lambda: self.placeholder_action("Manage Books"))

        # Member Menu
        member_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Members", menu=member_menu)
        member_menu.add_command(label="Register New Member", command=lambda: self.notebook.select(2))
        member_menu.add_command(label="Manage Members", command=lambda: self.placeholder_action("Manage Members"))

        # Transaction Menu
        transaction_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transactions", menu=transaction_menu)
        transaction_menu.add_command(label="Issue Book", command=lambda: self.notebook.select(3))
        transaction_menu.add_command(label="Return Book", command=lambda: self.notebook.select(3))

        # Help Menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About LMS", command=lambda: self.placeholder_action("About LMS"))

    # --- Toolbar Implementation ---
    def create_toolbar(self):
        toolbar = Frame(self.master, bd=1, relief=tk.RAISED)
        self.add_button(toolbar, "Issue Book", lambda: self.notebook.select(3), SUCCESS_COLOR)
        self.add_button(toolbar, "Return Book", lambda: self.notebook.select(3), DANGER_COLOR)
        self.add_button(toolbar, "Add Book", lambda: self.notebook.select(1), PRIMARY_COLOR)
        self.add_button(toolbar, "Add Member", lambda: self.notebook.select(2), SECONDARY_COLOR)
        toolbar.pack(side=tk.TOP, fill=tk.X)

    def add_button(self, parent, text, command, color):
        button = Button(parent, text=text, fg="white", bg=color, command=command, font=(FONT_FAMILY, 10, 'bold'))
        button.pack(side=tk.LEFT, padx=5, pady=5)

    # --- Tabbed Sections ---
    def create_dashboard_tab(self):
        dashboard_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(dashboard_frame, text="Dashboard")
        ttk.Label(dashboard_frame, text="Dashboard: Key Statistics", style="Header.TLabel").pack(pady=20)
        
        # Statistics Frame
        stats_frame = ttk.Frame(dashboard_frame)
        stats_frame.pack(pady=10)
        
        self.total_books_var = tk.StringVar()
        self.total_members_var = tk.StringVar()
        self.books_on_loan_var = tk.StringVar()
        
        ttk.Label(stats_frame, text="Total Books:", font=(self.FONT_FAMILY, 12, 'bold')).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(stats_frame, textvariable=self.total_books_var, font=(self.FONT_FAMILY, 12)).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(stats_frame, text="Total Members:", font=(self.FONT_FAMILY, 12, 'bold')).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(stats_frame, textvariable=self.total_members_var, font=(self.FONT_FAMILY, 12)).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(stats_frame, text="Books on Loan:", font=(self.FONT_FAMILY, 12, 'bold')).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(stats_frame, textvariable=self.books_on_loan_var, font=(self.FONT_FAMILY, 12)).grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Separator(dashboard_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Report and Action Buttons Frame
        button_frame = ttk.Frame(dashboard_frame)
        button_frame.pack(pady=10)
        
        # Overdue Report Button
        ttk.Button(button_frame, text="View Overdue Books Report", command=self.show_overdue_report, style="AddBook.TButton").pack(side=tk.LEFT, padx=10)
        
        # Send Reminders Button
        ttk.Button(button_frame, text="Send Due Date Reminders", command=self.handle_send_reminders, style="Lookup.TButton").pack(side=tk.LEFT, padx=10)
        
        self.update_dashboard_stats()

    def update_dashboard_stats(self):
        from lms_models import get_dashboard_stats
        stats = get_dashboard_stats(self.db_session)
        self.total_books_var.set(stats["total_books"])
        self.total_members_var.set(stats["total_members"])
        self.books_on_loan_var.set(stats["books_on_loan"])

    def handle_send_reminders(self):
        from lms_models import send_due_date_reminders
        
        # The send_due_date_reminders function handles both upcoming and overdue alerts
        summary = send_due_date_reminders(self.db_session)
        
        messagebox.showinfo(
            "Reminders Sent",
            f"Notification Summary:\n\n"
            f"Reminders for books due soon: {summary['reminders_sent']} sent.\n"
            f"Alerts for overdue books: {summary['overdue_alerts_sent']} sent.\n\n"
            f"Check the console for simulated SMS/Email content."
        )

    def show_overdue_report(self):
        from lms_models import get_overdue_transactions
        overdue_list = get_overdue_transactions(self.db_session)
        
        if not overdue_list:
            messagebox.showinfo("Overdue Report", "No books are currently overdue.")
            return

        # Create a new Toplevel window for the report
        report_window = tk.Toplevel(self.master)
        report_window.title("Overdue Books Report")
        report_window.geometry("800x400")
        
        ttk.Label(report_window, text="Overdue Books", style="Header.TLabel").pack(pady=10)

        # Treeview for tabular data
        tree = ttk.Treeview(report_window, columns=("ID", "Title", "Member", "Due Date", "Overdue Days"), show="headings")
        tree.heading("ID", text="Trans. ID")
        tree.heading("Title", text="Book Title")
        tree.heading("Member", text="Member Name")
        tree.heading("Due Date", text="Due Date")
        tree.heading("Overdue Days", text="Overdue Days")
        
        # Set column widths
        tree.column("ID", width=70, anchor="center")
        tree.column("Title", width=250)
        tree.column("Member", width=150)
        tree.column("Due Date", width=100, anchor="center")
        tree.column("Overdue Days", width=100, anchor="center")

        for item in overdue_list:
            tree.insert("", tk.END, values=(
                item["transaction_id"],
                item["book_title"],
                item["member_name"],
                item["due_date"],
                item["overdue_days"]
            ))

        tree.pack(expand=True, fill="both", padx=10, pady=10)
        
    def create_book_management_tab(self):
        book_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(book_frame, text="Book Management")
        ttk.Label(book_frame, text="Book Management", style="Header.TLabel").pack(pady=10)
        
        # Notebook for Book Management Tabs
        book_notebook = ttk.Notebook(book_frame)
        book_notebook.pack(expand=True, fill="both")
        
        # Tab 1: ISBN Lookup
        lookup_tab = ttk.Frame(book_notebook, padding="10 10 10 10")
        book_notebook.add(lookup_tab, text="Add Book (ISBN Lookup)")
     def create_book_management_tab(self):
        book_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(book_frame, text="Book Management")
        ttk.Label(book_frame, text="Book Management", style="Header.TLabel").pack(pady=10)
        
        # Notebook for Book Management Tabs
        book_notebook = ttk.Notebook(book_frame)
        book_notebook.pack(expand=True, fill="both")
        
        # Tab 1: ISBN Lookup
        lookup_tab = ttk.Frame(book_notebook, padding="10 10 10 10")
        book_notebook.add(lookup_tab, text="Add Book (ISBN Lookup)")
        self.create_isbn_lookup_section(lookup_tab)
        
        # Tab 2: View All Books
        view_tab = ttk.Frame(book_notebook, padding="10 10 10 10")
        book_notebook.add(view_tab, text="View All Books")
        self.create_view_all_books_section(view_tab)

    def create_isbn_lookup_section(self, parent):
        lookup_frame = ttk.LabelFrame(parent, text="ISBN Lookup", padding="10 10 10 10")
        lookup_frame.pack(fill="x", pady=10)
        
        ttk.Label(lookup_frame, text="Enter ISBN:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.isbn_entry = ttk.Entry(lookup_frame, width=20)
        self.isbn_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Button(lookup_frame, text="Lookup Book", command=self.handle_isbn_lookup).grid(row=0, column=2, padx=10, pady=5)
        
        details_frame = ttk.LabelFrame(parent, text="Book Details", padding="10 10 10 10")
        details_frame.pack(fill="x", pady=10)
        
        self.book_details_vars = {"Title": tk.StringVar(value="N/A"), "Author": tk.StringVar(value="N/A"), "Publisher": tk.StringVar(value="N/A"), "Year": tk.StringVar(value="N/A")}
        self.cover_image_label = ttk.Label(details_frame)
        self.cover_image_label.grid(row=0, column=2, rowspan=len(self.book_details_vars)+1, padx=10, pady=5)
        self.cover_image_tk = None # To prevent garbage collection
        
        for i, (label_text, var) in enumerate(self.book_details_vars.items()):
            ttk.Label(details_frame, text=f"{label_text}:", font=(self.FONT_FAMILY, 10, 'bold')).grid(row=i, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(details_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=2, sticky="w")
            
        self.add_book_button = ttk.Button(details_frame, text="Add Book to Library", command=self.handle_add_book_to_db, state=tk.DISABLED)
        self.add_book_button.grid(row=len(self.book_details_vars), column=0, columnspan=2, pady=10)

    def create_view_all_books_section(self, parent):
        # Treeview for displaying all books
        self.book_tree = ttk.Treeview(parent, columns=("ID", "Title", "Author", "ISBN", "Total", "Available"), show="headings")
        self.book_tree.heading("ID", text="ID")
        self.book_tree.heading("Title", text="Title")
        self.book_tree.heading("Author", text="Author")
        self.book_tree.heading("ISBN", text="ISBN")
        self.book_tree.heading("Total", text="Total Copies")
        self.book_tree.heading("Available", text="Available")
        
        self.book_tree.column("ID", width=50, anchor="center")
        self.book_tree.column("Title", width=250)
        self.book_tree.column("Author", width=150)
        self.book_tree.column("ISBN", width=120)
        self.book_tree.column("Total", width=80, anchor="center")
        self.book_tree.column("Available", width=80, anchor="center")
        
        self.book_tree.pack(expand=True, fill="both")
        
        ttk.Button(parent, text="Refresh Book List", command=self.refresh_book_list).pack(pady=5)
        
        self.refresh_book_list()

    def refresh_book_list(self):
        from lms_models import get_all_books
        
        # Clear existing data
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)
            
        books = get_all_books(self.db_session)
        for book in books:
            self.book_tree.insert("", tk.END, values=(
                book.book_id,
                book.title,
                book.author,
                book.isbn,
                book.total_copies,
                book.available_copies
            ))  def handle_isbn_lookup(self):
        isbn = self.isbn_entry.get().strip()
        if not isbn: return messagebox.showerror("Error", "Please enter an ISBN.")
        result = lookup_book_by_isbn(isbn)
        if result.get("success"):
            messagebox.showinfo("Success", f"Book found: {result['title']}")
            self.update_book_details_display(result)
            self.display_book_cover(result.get("cover_image_url"))
            self.add_book_button.config(state=tk.NORMAL)
            self.last_lookup_data = result
        else:
            messagebox.showerror("Error", result.get("message", "Book not found."))
            self.update_book_details_display({})
            self.display_book_cover(None)
            self.add_book_button.config(state=tk.DISABLED)
            self.last_lookup_data = None

    def update_book_details_display(self, data):
        for key, var in self.book_details_vars.items():
            var.set(data.get(key.lower().replace(' ', '_'), "N/A"))

    def display_book_cover(self, url):
        """Downloads and displays the book cover image."""
        self.cover_image_label.config(image='') # Clear previous image
        self.cover_image_tk = None
        
        if not url:
            self.cover_image_label.config(text="No Cover")
            return

        try:
            # Download image
            response = requests.get(url, stream=True)
            response.raise_for_status()
            image_data = response.content
            
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Resize image to fit the display area (e.g., 100x150)
            max_size = (100, 150)
            image.thumbnail(max_size)
            
            # Convert to Tkinter PhotoImage
            self.cover_image_tk = ImageTk.PhotoImage(image)
            
            # Display image
            self.cover_image_label.config(image=self.cover_image_tk, text='')
            
        except Exception as e:
            self.cover_image_label.config(text="Image Error")
            print(f"Error displaying image: {e}")

    def handle_add_book_to_db(self):
        if self.last_lookup_data:
            try:
                new_book = add_book_to_db(self.db_session, self.last_lookup_data)
                messagebox.showinfo("Success", f"Book '{new_book.title}' added/updated! Available copies: {new_book.available_copies}")
                self.add_book_button.config(state=tk.DISABLED)
                self.isbn_entry.delete(0, tk.END)
                self.update_book_details_display({})
                self.refresh_book_list() # Refresh the list after adding
                self.update_dashboard_stats() # Update stats
            except Exception as e:
                messagebox.showerror("DB Error", f"Failed to add book: {e}")

    def create_member_management_tab(self):
        member_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(member_frame, text="Member Management")
        ttk.Label(member_frame, text="Member Management", style="Header.TLabel").pack(pady=10)
        
        # Notebook for Member Management Tabs
        member_notebook = ttk.Notebook(member_frame)
        member_notebook.pack(expand=True, fill="both")
        
        # Tab 1: Registration
        reg_tab = ttk.Frame(member_notebook, padding="10 10 10 10")
        member_notebook.add(reg_tab, text="Register New Member")
        self.create_member_registration_form(reg_tab)
        
        # Tab 2: View All Members
        view_tab = ttk.Frame(member_notebook, padding="10 10 10 10")
        member_notebook.add(view_tab, text="View All Members")
        self.create_view_all_members_section(view_tab)

    def create_view_all_members_section(self, parent):
        # Treeview for displaying all members
        self.member_tree = ttk.Treeview(parent, columns=("ID", "Name", "Membership No.", "Email", "Phone"), show="headings")
        self.member_tree.heading("ID", text="ID")
        self.member_tree.heading("Name", text="Name")
        self.member_tree.heading("Membership No.", text="Membership No.")
        self.member_tree.heading("Email", text="Email")
        self.member_tree.heading("Phone", text="Phone")
        
        self.member_tree.column("ID", width=50, anchor="center")
        self.member_tree.column("Name", width=150)
        self.member_tree.column("Membership No.", width=120)
        self.member_tree.column("Email", width=200)
        self.member_tree.column("Phone", width=100)
        
        self.member_tree.pack(expand=True, fill="both")
        
        ttk.Button(parent, text="Refresh Member List", command=self.refresh_member_list).pack(pady=5)
        
        self.refresh_member_list()

    def refresh_member_list(self):
        from lms_models import get_all_members
        
        # Clear existing data
        for item in self.member_tree.get_children():
            self.member_tree.delete(item)
            
        members = get_all_members(self.db_session)
        for member in members:
            self.member_tree.insert("", tk.END, values=(
                member.member_id,
                f"{member.first_name} {member.last_name}",
                member.membership_number,
                member.email,
                member.phone
            ))
        
        self.create_member_registration_form(member_frame)

    def create_member_registration_form(self, parent):
        form_frame = ttk.LabelFrame(parent, text="Member Details", padding="10 10 10 10")
        form_frame.pack(fill="x", pady=10, padx=50)

        self.member_vars = {
            "First Name": tk.StringVar(),
            "Last Name": tk.StringVar(),
            "Email": tk.StringVar(),
            "Phone": tk.StringVar(),
            "Membership No.": tk.StringVar(),
        }

        row_num = 0
        for label_text, var in self.member_vars.items():
            ttk.Label(form_frame, text=f"{label_text}:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
            ttk.Entry(form_frame, textvariable=var, width=40).grid(row=row_num, column=1, padx=5, pady=5, sticky="w")
            row_num += 1

        ttk.Button(form_frame, text="Register Member", command=self.handle_register_member, style="AddBook.TButton").grid(row=row_num, column=0, columnspan=2, pady=15)

    def handle_register_member(self):
        data = {k: v.get() for k, v in self.member_vars.items()}
        
        if not all(data.values()):
            messagebox.showerror("Error", "All fields are required for registration.")
            return

        try:
            new_member = Member(
                membership_number=data["Membership No."],
                first_name=data["First Name"],
                last_name=data["Last Name"],
                email=data["Email"],
                phone=data["Phone"]
            )
            self.db_session.add(new_member)
            self.db_session.commit()
            messagebox.showinfo("Success", f"Member {new_member.first_name} {new_member.last_name} registered successfully! ID: {new_member.member_id}")
            
            # Clear form
            for var in self.member_vars.values():
                var.set("")
            
            self.refresh_member_list() # Refresh the list after adding
            self.update_dashboard_stats() # Update stats after registration

        except Exception as e:
            self.db_session.rollback()
            messagebox.showerror("DB Error", f"Failed to register member. Check if Membership No. or Email is already in use.\nError: {e}")

    def create_transaction_management_tab(self):
        transaction_frame = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(transaction_frame, text="Transactions")
        ttk.Label(transaction_frame, text="Issue & Return Books", style="Header.TLabel").pack(pady=10)
        self.create_issue_book_form(transaction_frame)
        self.create_return_book_form(transaction_frame)

    def create_issue_book_form(self, parent):
        issue_frame = ttk.LabelFrame(parent, text="Issue Book", padding="10 10 10 10")
        issue_frame.pack(fill="x", pady=10, side=tk.LEFT, expand=True, anchor="n")
        self.issue_vars = {"Member ID": tk.StringVar(), "Book ID": tk.StringVar()}
        for i, (label_text, var) in enumerate(self.issue_vars.items()):
            ttk.Label(issue_frame, text=f"{label_text}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            ttk.Entry(issue_frame, textvariable=var, width=20).grid(row=i, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(issue_frame, text="Issue Book", command=self.handle_issue_book).grid(row=len(self.issue_vars), column=0, columnspan=2, pady=10)

    def handle_issue_book(self):
        try:
            member_id, book_id = int(self.issue_vars["Member ID"].get()), int(self.issue_vars["Book ID"].get())
        except ValueError: return messagebox.showerror("Input Error", "IDs must be numbers.")
        result = issue_book(self.db_session, member_id, book_id)
        messagebox.showinfo("Result", result["message"]) if result["success"] else messagebox.showerror("Error", result["message"])
        self.update_dashboard_stats() # Update stats after issue
        self.refresh_book_list() # Refresh book list to show updated available copies

    def create_return_book_form(self, parent):
        return_frame = ttk.LabelFrame(parent, text="Return Book", padding="10 10 10 10")
        return_frame.pack(fill="x", pady=10, side=tk.RIGHT, expand=True, anchor="n")
        self.return_var = tk.StringVar()
        ttk.Label(return_frame, text="Transaction ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(return_frame, textvariable=self.return_var, width=20).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(return_frame, text="Return Book", command=self.handle_return_book).grid(row=1, column=0, columnspan=2, pady=10)

    def handle_return_book(self):
        try: transaction_id = int(self.return_var.get())
        except ValueError: return messagebox.showerror("Input Error", "ID must be a number.")
        result = return_book(self.db_session, transaction_id)
        if result["success"]:
            fine_msg = f"Fine: ${result['fine_amount']:.2f}" if result['fine_amount'] > 0 else "No fine."
            messagebox.showinfo("Success", f"{result['message']}\n{fine_msg}")
            self.update_dashboard_stats() # Update stats after return
            self.refresh_book_list() # Refresh book list to show updated available copies
        else: messagebox.showerror("Error", result["message"])

    def create_status_bar(self):
        self.db_status, self.api_status = tk.StringVar(), tk.StringVar()
        status_bar = ttk.Frame(self.master, padding="3 3 3 3", relief=tk.SUNKEN)
        ttk.Label(status_bar, textvariable=self.db_status, style="Status.TLabel").pack(side=tk.LEFT, padx=10)
        ttk.Label(status_bar, textvariable=self.api_status, style="Status.TLabel").pack(side=tk.LEFT, padx=10)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def update_status_simulated(self):
        self.db_status.set("Database: Connected")
        self.api_status.set("API: Ready")

    def load_initial_data(self):
        if not self.db_session.query(Member).first():
            self.db_session.add(Member(membership_number="M001", first_name="Alice", last_name="Smith"))
            self.db_session.commit()
            messagebox.showinfo("Setup", "Dummy Member (ID: 1) added for testing.")
        if not self.db_session.query(Book).first():
            book_data = lookup_book_by_isbn("9780345391803")
            if book_data["success"]: add_book_to_db(self.db_session, book_data)
            messagebox.showinfo("Setup", "Dummy Book (ID: 1) added for testing.")

    def placeholder_action(self, name): messagebox.showinfo("Action", f"{name} not implemented.")
    def on_exit(self):
        if messagebox.askyesno("Exit", "Are you sure?"):
            self.db_session.close()
            self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = LMSApp(root)
    root.mainloop()
