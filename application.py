import os

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    """Show homepage with book search"""
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="You must provide a username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="You must provide a password.")

        # Query database for username, ensure it exists
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": request.form.get("username")}).fetchone()

        if user is None:
            return render_template("error.html", message="This username does not exist.")

        # Check that password is correct
        if not check_password_hash(user.hash, request.form.get("password")):
            return render_template("error.html", message="Invalid password!")

        # Remember which user has logged in
        session["user_id"] = user.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="You must provide a username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="You must provide a password.")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="Confirm password.")

        # Ensure username is unique (not case sensitive)
        usernames = db.execute("SELECT username FROM users")
        for user in usernames:
            if request.form.get("username") == user["username"]:
                return render_template("error.html", message="This username already exists.")

        # Ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("error.html", message="Passwords do not match.")

        # Insert valid username into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username": request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))})
        db.commit()

        # Remember which user has logged in
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": request.form.get("username")}).fetchone()

        session["user_id"] = user.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("register.html")

@app.route("/search", methods=["POST"])
@login_required
def search():
    """Search for book"""

    # Get search information
    query = request.form.get("query")
    type = request.form.get("type")

    # Send error message if improper entries
    if not query or not type:
        return render_template("error.html", message="Invalid search.")

    # Prep for sanitation
    query = '%' + query + '%'

    # Query database depending on type
    if type == "ISBN":
        results = db.execute("SELECT * FROM books WHERE isbn LIKE :query", {"query": query})
    elif type == "Title":
        results = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE LOWER(:query)", {"query": query})
    elif type == "Author":
        results = db.execute("SELECT * FROM books WHERE LOWER(author) LIKE LOWER(:query)", {"query": query})
    else:
        results = None;

    return render_template("search.html", results=results)

@app.route("/book/<int:book_id>", methods=["GET", "POST"])
@login_required
def book(book_id):
    """Display book info"""

    # Find book
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="No such book.")

    # Get all reviews
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()

    return render_template("book.html", book=book, reviews=reviews)

@app.route("/review/<int:book_id>", methods=["GET", "POST"])
@login_required
def review(book_id):
    """Form for book review"""
    # Keep track of user
    user_id = session["user_id"]

    # Find book
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="No such book.")

    # User reached route via GET (as by clicking the Write a Review button)
    if request.method == "GET":
        # Throw error message if user has already submitted a review
        if db.execute("SELECT user_id FROM reviews WHERE user_id = :user_id", {"user_id": user_id}).rowcount != 0:
            return render_template("error.html", message="You may only submit one review per book.")

        return render_template("review.html", book=book)

    # User reached route via POST (as by submitting a form via POST)
    else:
        # Collect rating and review from form
        rating = request.form.get("optradio")
        text = request.form.get("review")

        # Throw error message if improper entries
        if not rating or not text:
            return render_template("error.html", message="You must complete the rating.")

        # Insert review into database
        db.execute("INSERT INTO reviews (rating, text, book_id, user_id) VALUES (:rating, :text, :book_id, :user_id)", {"rating": rating, "text": text, "book_id": book_id, "user_id": user_id})
        db.commit()
        return render_template("submit.html", book=book)
