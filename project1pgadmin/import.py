import csv, os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
  raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    print(type(f))
    reader = csv.reader(f)
    print(type(reader))
    #db.execute("CREATE TABLE thebook(isbn varchar(30), title varchar(100),author varchar(100),year varchar(10))")
    for isbn, title, author, year in reader:
         db.execute("INSERT INTO thebook1(isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",{"isbn": isbn, "title": title, "author": author, "year": year})
         db.commit()

if __name__ == "__main__":
  main()