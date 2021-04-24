import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import json
from classes import User, Book


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


@app.route("/index")
def index():
    return render_template("index.html", user=session["user"])


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        name = request.form.get("username")
        email= request.form.get("password")
        result = db.execute("SELECT name, email FROM users WHERE name=:name AND email=:email", {"name": name, "email": email}).fetchone()
        if result is None:
        	return render_template("login.html")
        else:
            user = User(result.name, result.email)
            
        
            if user:
                session["user"] = user
                return render_template("index.html", user=user)
    
    return render_template("login.html", notShow=True)

@app.route("/register", methods=["GET", "POST"])
def  register():
    if request.method == 'GET':
        return render_template("register.html", notShow=True)
    else:
        name = request.form.get("name")
        #username = request.form.get("username")
        #email = request.form.get("email")
        email = request.form.get("password")
        #db.execute("INSERT INTO users(name, email) VALUES (:name, :email)", {"name": name, "email": email})
        db.execute("INSERT INTO users(name, email) VALUES (:name, :email)", {"name": name, "email": email})
        db.commit()
        return render_template("login.html")

@app.route("/layout")
def layout():
    return render_template("layout.html")

@app.route("/logout")
def logout():
    session["user"] = None
    return redirect(url_for("login"))


@app.route("/books", methods=["GET", "POST"])
def books():
    if session["user"] is None:
        return login()

    
    if request.method == "GET":
        books = db.execute("SELECT * FROM thebook1").fetchmany(10)
        return render_template("books.html", books=books)
    else:

        text = "%"+request.form.get("search-text")+"%"
        books = db.execute("SELECT * FROM thebook1 WHERE (isbn LIKE :isbn OR title LIKE :title OR author LIKE :author OR year LIKE :year)", {"isbn":text, "title":text, "author":text, "year":text}).fetchall()
        return render_template("books.html", books=books, search=text.replace('%', ''))




@app.route("/details/<string:isbn>", methods=["GET", "POST"])
def details(isbn):
    if session["user"] is None:
        return login()

    book = Book()
    
    book.isbn, book.title, book.author, book.year, book.reviews_count, book.average_rating = db.execute("SELECT isbn, title, author, year, reviews_count, average_rating FROM thebook1 WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    if book.average_rating==0 or book.reviews_count==0:
        book_aux = api_intern(isbn)
        
        book.average_rating = book_aux["thebook1"][0]["average_rating"]
        book.reviews_count = book_aux["thebook1"][0]["reviews_count"]
        db.execute("UPDATE thebook1 SET average_rating = :average_rating, reviews_count = :reviews_count WHERE isbn=:isbn", {"isbn": isbn, "average_rating": float(book.average_rating), "reviews_count": int(book.reviews_count)})

        db.commit()
    if request.method == "GET":
        return render_template("details.html", book=book)
    else:
        return "POST DETAILS"


@app.route("/review/<string:isbn>", methods=["GET", "POST"])
def review(isbn):
    if session["user"] is None:
        return login()

    book = db.execute("SELECT * FROM thebook1 WHERE isbn= :isbn"
        , {"isbn": isbn}).fetchone()
    if request.method == "POST":
        review = request.form.get("review")
        score = request.form.get("score")
        """ Calculating new average rating and number of reviews from the book """
        average_rating = float(score)/2
        reviews_count = 1
        comments = db.execute("SELECT * FROM reviews WHERE author_id= :author_id AND book_isbn= :book_isbn", {"author_id": session["user"].id, "book_isbn": isbn}).fetchone()

        
        if comments is not None:
            return render_template("error.html", message="You already posted a comment to this book", url_return='review/'+isbn, page_name='review')

        db.execute("INSERT INTO reviews(review, score, author_id, book_isbn) VALUES (:review, :score, :author_id, :book_isbn)", {"review": review, "score": score, "author_id": session["user"].id, "book_isbn": isbn})
        db.execute("UPDATE thebook1 SET average_rating = :average_rating, reviews_count = :reviews_count WHERE isbn=:isbn", {"isbn": isbn, "average_rating": average_rating, "reviews_count": reviews_count})

        db.commit()

    reviews = db.execute("SELECT * FROM reviews WHERE book_isbn= :isbn"
        , {"isbn": isbn}).fetchall()
    return render_template("review.html", book=book, reviews=reviews)


@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    """ Give all the details about the book"""
    if request.method == "GET":
        res = db.execute("SELECT title, author, year, isbn, reviews_count, average_rating FROM thebook1 WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        book = Book()

        if res is None:
            return render_template("error.html", message="404 error", url_return='/', page_name='index'), 404
        
        book.title, book.author, book.year, book.isbn, book.reviews_count, book.average_rating = res
        if res.reviews_count==0 or res.average_rating==0:
            book_aux = api_intern(isbn)
            book.average_rating = book_aux["books"][0]["average_rating"]
            book.reviews_count = book_aux["books"][0]["reviews_count"]

        response = {"title": book.title, "author": book.author, "year": book.year, "isbn": book.isbn, "review_count": book.reviews_count, "average_score": book.average_rating}
        return jsonify(response)



def api_intern(isbn):

    res = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn", params={"key": "AIzaSyCA_nRXODIrd8WIvmX_jErSseesHvk0JHY", "isbns": isbn})

    return res.json()
    
    
    


