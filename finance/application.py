import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

from datetime import datetime
import pytz

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

info=[]

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    index = db.execute("SELECT * FROM 'buy' WHERE user_id = :user_id",
                       user_id = session["user_id"])

    user = db.execute("SELECT * FROM 'users' WHERE id = :user_id",
                      user_id = session["user_id"])

    if not user:
        left = 10000

    else:
        left = user[0]["cash"]

    sum = left

    for x in index:
        current = x["share_symbol"]
        info=lookup(current)

        x["price"] = info["price"]
        x["total"] = info["price"] * x["number_bought"]
        sum = sum + x["total"]


    return render_template("index.html", index=index, sum=sum, left=left)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":


        # Ensure username was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Ensure Shares field is not empty
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 403)

        shares = int(request.form.get("shares"))
        if not shares > 0:
            return apology("must provide a positive number", 403)

        info=lookup(request.form.get("symbol"))

        #Ensure symbol is valid
        if not info:
            return apology("invalid symbol", 403)

        rows = db.execute("SELECT * FROM users WHERE id = :user_id",
                          user_id=session["user_id"])

        cash = rows[0]["cash"]

        if shares * (info["price"]) > cash:
            return apology("cannot afford", 403)

        # datetime object containing current date and time
        tz = pytz.timezone('GMT')
        now = datetime.now(tz)
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")


        user = db.execute("SELECT * FROM buy WHERE user_id = :id AND share_bought = :share_bought",
                          id = session["user_id"], share_bought = info["name"])

        if not user:
            db.execute("INSERT INTO 'buy' (user_id, username, share_bought, share_symbol, number_bought, price, total) VALUES (:id, :username, :share, :symbol, :number, :price, :cash)",
                       id = session["user_id"], username = session["username"], share = info["name"], symbol = info["symbol"], number = shares, price = info["price"], cash = shares * info["price"])


        else:
            number = user[0]["number_bought"] + shares
            total_cash = user[0]["total"] + (shares * info["price"])
            db.execute("UPDATE buy SET number_bought = :number, total = :cash WHERE user_id = :id AND share_bought = :share_bought",
                       number = number, cash = total_cash, id = session["user_id"], share_bought = info["name"])

        db.execute("UPDATE users SET cash = :total WHERE id = :user_id",
                   total = cash - (shares * info["price"]), user_id=session["user_id"])

        db.execute("INSERT INTO 'time' (user_id, symbol, shares, price, time) VALUES (:user_id, :symbol, :shares, :price, :time)",
                  user_id = session["user_id"], symbol = info["symbol"], shares = shares, price = info["price"], time = dt_string)

        flash("Bought!")
        return redirect ("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    history = db.execute("SELECT * FROM 'time' WHERE user_id = :id",
                         id = session["user_id"])
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

         # Ensure username was submitted
        if not request.form.get("symbol"):
            return apology("missing symbol", 403)

        info=lookup(request.form.get("symbol"))

        #Ensure symbol is valid
        if not info:
            return apology("invalid symbol", 403)

        return render_template("quoted.html", info=info)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        #Ensure both password fields have the same value
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password does not match with confirmed password", 403)

        #Ensure username does not exist
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) != 0:
            return apology("username already exists", 403)

        password = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   username=request.form.get("username"), hash=password)

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        flash("Registered!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    if request.method == "GET":

        rows = db.execute("SELECT * FROM 'buy' WHERE user_id = :user_id",
                          user_id = session["user_id"])
        return render_template("sell.html", rows=rows)

    else:

        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Ensure Shares field is not empty
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 403)

        shares = int(request.form.get("shares"))
        if not shares > 0:
            return apology("must provide a positive number", 403)

        info=lookup(request.form.get("symbol"))

        #Ensure symbol is valid
        if not info:
            return apology("invalid symbol", 403)

        # datetime object containing current date and time
        tz = pytz.timezone('GMT')
        now = datetime.now(tz)
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        share = db.execute("SELECT * FROM 'buy' WHERE user_id = :user_id AND share_symbol = :share_symbol",
                           user_id = session["user_id"], share_symbol = request.form.get("symbol"))

        user = db.execute("SELECT * FROM 'users' WHERE id = :id",
                          id = session["user_id"])

        if share[0]["number_bought"] < shares:
            return apology("too many shares", 403)

        else:
            num = share[0]["number_bought"] - shares
            db.execute("UPDATE buy SET number_bought = :number_bought, price = :price, total = :total WHERE user_id = :id AND share_symbol = :share_symbol",
                       number_bought = num, price = info["price"], total = num * info["price"], id = session["user_id"], share_symbol = request.form.get("symbol"))

            db.execute("UPDATE users SET cash = :cash WHERE id = :id",
                       cash = user[0]["cash"] + shares*info["price"], id = session["user_id"])

            db.execute("INSERT INTO 'time' (user_id, symbol, shares, price, time) VALUES (:user_id, :symbol, :shares, :price, :time)",
                  user_id = session["user_id"], symbol = info["symbol"], shares = (-1) * shares, price = info["price"], time = dt_string)

        flash("Sold!")
        return redirect("/")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change Password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure old password was submitted
        if not request.form.get("old_password"):
            return apology("must provide old password", 403)

        # Ensure new password was submitted
        elif not request.form.get("new_password"):
            return apology("must provide new password", 403)

        # Ensure password was confirmed
        elif not request.form.get("confirm_password"):
            return apology("must confirm password", 403)

        #Ensure both password fields have the same value
        elif request.form.get("new_password") != request.form.get("confirm_password"):
            return apology("new password does not match with confirmed password", 403)

        #Ensure username does not exist
        rows = db.execute("SELECT * FROM users WHERE id = :user_id",
                          user_id=session["user_id"])

        old = generate_password_hash(request.form.get("old_password"))

        # Ensure old password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("old_password")):
            return apology("invalid password", 403)

        new = generate_password_hash(request.form.get("new_password"))

        db.execute("UPDATE users SET hash = :hash WHERE id = :user_id",
                   hash=new, user_id=session["user_id"])

        flash("Password Changed!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
