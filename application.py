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
	"""Show user homepage"""

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
			return render_template("error.html", message="must provide username")

        # Ensure password was submitted
		elif not request.form.get("password"):
			return render_template("error.html", message="must provide password")

        # Query database for username, ensure it exists
		user = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()
		if user is None:
			return render_template("error.html", message="username does not exist")

        # Check that password is correct
		if not check_password_hash({rows.hash}, request.form.get("password")):
			return render_template("error.html", message="invalid password")

        # Remember which user has logged in
		session["user_id"] = {rows.id}

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
            return render_template("error.html", message="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="must provide password")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="confirm password")

        # Ensure username is unique (not case sensitive)
        usernames = db.execute("SELECT username FROM users")
        for user in usernames:
            if request.form.get("username") == user["username"]:
                return render_template("error.html", message="username already exists")

        # Ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("error.html", message="passwords do not match")

        # Insert valid username into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   {"username": request.form.get("username"),
				   "hash": generate_password_hash(request.form.get("password"))})

        # Remember which user has logged in
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        session["user_id"] = {rows.id}

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("register.html")
