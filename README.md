# Project 1: Books

CS50: Web Programming with Python and JavaScript

This is COADBOOKS, a Flask application built to search for and review books. I used the CS50 Finance app I made in the CS50 Web Track as a starting point for this project. Specifically, my login and registration routes were based heavily on the ones I used in CS50, as they generated and checked password hashes for a more secure session.

"import.py" & "books.csv"
    The books in the database were imported using "import.py", a short Python program that takes "books.csv" and imports the 5001 books contained within into my database stored on Heroku.

"create.sql"
    Contained in this file are the SQL commands used to create the three tables in the coadbooks database: users, books, and reviews.

"application.py"
    This is the python program that runs the flask application. (Set the environment variable FLASK_APP to be application.py. Additionally, DATABASE_URL and API_KEY must be set for the program to run, but I have not included those here for security purposes.)

    application.py sets up a session for the user and contains all the routes to the different pages of the application. See the code for the routes.

"static" & "templates" folders
    Finally, the "static" and "templates" folders contain the HTML and CSS to make this app function (and stylish).

    Within "templates" are the HTML pages that are displayed as the result of a GET or POST request. "layout.html" holds the base layout for all the pages. Each of the other pages extends "layout.html".

    Within "static" is the books icon, the books favicon, and the styles for the HTML pages.
