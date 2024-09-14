from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
import pytz

from helper import (
    process_data, apology, fetch_barcode, fix_time,
    login_required, insert_product, insert_search, validate_data,
    insert_settings, sort_by_search_time, insert_user_product
)

app = Flask(__name__)

# Configure session to use the filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")

settings = {
    "darkmode": "on",
    "timezone": pytz.all_timezones[0],
}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    update_settings()
    saved = []
    # Grab all users saved products to show as autocomplete
    if session.get("user_id"):
        saved = db.execute("SELECT * FROM user_products, products WHERE user_id = ? AND product_id = id", session["user_id"])
    return render_template("index.html", saved=saved)


@app.route("/search_barcode", methods=["GET"])
def search_barcode():
    barcode = request.args.get("barcode")
    if not barcode:
        return apology("Missing barcode", 403)

    # Check barcode exits in db
    rows = db.execute("SELECT * FROM products WHERE id = ?", barcode)
    if len(rows) == 0:
        # Barcode did not exist grab it and add to local db
        print(f"Searching for {barcode} online")
        response = fetch_barcode(barcode)
        if response.status_code != 200:
            return apology("Could not find product", response.status_code)
        data = process_data(response.json())
        if not validate_data(data):
            return apology("Product is missing data", 404)
        insert_product(db, data)
    else:
        # barcode exits
        print(f"Found {barcode} localy")
    rows = db.execute("SELECT * FROM products WHERE id = ?", barcode)
    data = rows[0]

    is_saved = False
    # Add search to history
    if session.get("user_id"):
        insert_search(db, session["user_id"], barcode)
        saved = db.execute("SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], barcode)
        is_saved = len(saved) != 0
        print("User id found :)")
    else:
        print("No user id")
    update_settings()
    return render_template("product.html", data=data, is_saved=is_saved)


@app.route("/compare_products", methods=["GET"])
def compare_products():
    # TODO: Clean up this mess
    # ---Barcode a---
    barcode_a = request.args.get("barcode_a")
    if not barcode_a:
        return apology("Missing barcode a", 403)
    # Check barcode_a exits in db
    rows_a = db.execute("SELECT * FROM products WHERE id = ?", barcode_a)
    if len(rows_a) == 0:
        # Barcode did not exist grab it and add to local db
        print(f"Searching for {barcode_a} online")
        response_a = fetch_barcode(barcode_a)
        if response_a.status_code != 200:
            return apology("Could not find product", response_a.status_code)
        data_a = process_data(response_a.json())
        if not validate_data(data_a):
            return apology("Product is missing data", 404)
        insert_product(db, data_a)
    else:
        print(f"Found {barcode_a} localy")
    rows_a = db.execute("SELECT * FROM products WHERE id = ?", barcode_a)
    data_a = rows_a[0]
    is_saved_a = False
    if session.get("user_id"):
        saved = db.execute("SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], barcode_a)
        is_saved_a = len(saved) != 0

    # ---Barcode b---
    barcode_b = request.args.get("barcode_b")
    if not barcode_b:
        return apology("Missing barcode b", 403)
    # Check barcode_b exits in db
    rows_b = db.execute("SELECT * FROM products WHERE id = ?", barcode_b)
    if len(rows_b) == 0:
        # Barcode did not exist grab it and add to local db
        print(f"Searching for {barcode_a} online")
        response_b = fetch_barcode(barcode_b)
        if response_b.status_code != 200:
            return apology("Could not find product", response_b.status_code)
        data_b = process_data(response_b.json())
        if not validate_data(data_a):
            return apology("Product is missing data", 404)
        insert_product(db, data_b)
    else:
        print(f"Found {barcode_a} localy")
    rows_b = db.execute("SELECT * FROM products WHERE id = ?", barcode_b)
    data_b = rows_b[0]
    is_saved_b = False
    if session.get("user_id"):
        saved = db.execute("SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], barcode_b)
        is_saved_b = len(saved) != 0

    # ---return information---
    update_settings()
    data_a = get_barcode_data(barcode_a)
    # if type
    return render_template("compare.html", data_a=data_a, is_saved_a=is_saved_a, data_b=data_b, is_saved_b=is_saved_b)


@app.route("/lists")
@login_required
def shopping_lists():
    saved = db.execute("SELECT * FROM user_products, products WHERE products.id = product_id AND user_id = ?", session["user_id"])
    return render_template("lists.html", saved=saved)


@app.route("/add_new_list", methods=["POST"])
@login_required
def new_shopping_list():
    # TODO: Add a new list to the db and redirect user to the new list
    return "NEW LIST"


def get_barcode_data(barcode):
    rows = db.execute("SELECT * FROM products WHERE id = ?", barcode)
    if len(rows) == 0:
        response = fetch_barcode(barcode)
        if response.status_code != 200:
            return apology("Could not find product", 404)
        data = process_data(response.json())
        if not validate_data(data):
            return apology("Product is missing data", 404)
        insert_product(db, data)
        rows = db.execute("SELECT * FROM products WHERE id = ?", barcode)
    data = rows[0]
    return data


@app.route("/history", methods=["GET"])
@login_required
def history():
    history = db.execute("SELECT * FROM user_searches, products WHERE user_id = ? AND product_id = products.id", session["user_id"])
    for i, search in enumerate(history):
        fixed_time = fix_time(search["search_time"], session["timezone"])
        history[i]["search_time"] = fixed_time
    history.sort(key=sort_by_search_time)
    history.reverse()
    update_settings()
    return render_template("history.html", history=history)


@app.route("/clear_history")
@login_required
def clear_history():
    db.execute("DELETE FROM user_searches WHERE user_id = ?", session["user_id"])
    return redirect("/history")


@app.route("/save", methods=["POST"])
@login_required
def save():
    product_id = request.form.get("id")
    if not product_id:
        return apology("Missing product id", 403)
    rows = db.execute("SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], product_id)
    if len(rows) != 0:
        return redirect("/saved")
    insert_user_product(db, session["user_id"], product_id)
    flash("Saved!")
    return redirect("/saved")


@app.route("/debug", methods=["GET"])
def debug():
    products = db.execute("SELECT * FROM products")
    return render_template("debug.html", products=products)


@app.route("/remove", methods=["POST"])
@login_required
def remove():
    product_id = request.form.get("id")
    if not product_id:
        return apology("Missing product id", 403)
    rows = db.execute("SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], product_id)
    if len(rows) == 0:
        return redirect("/saved")
    db.execute("DELETE FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], product_id)
    flash("Removed!")
    return redirect("/saved")


@app.route("/saved", methods=["GET"])
@login_required
def saved():
    saved = db.execute("SELECT * FROM user_products, products WHERE products.id = product_id AND user_id = ?", session["user_id"])
    return render_template("saved.html", saved=saved)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    user = user_rows[0]

    if request.method == "POST":
        username = request.form.get("username")
        darkmode = request.form.get("darkmode", "off")
        timezone = request.form.get("timezone")

        if not username:
            apology("Mising username", 400)

        if not darkmode:
            apology("Mising darkmode", 400)

        if not timezone:
            apology("Mising timezone", 400)

        db.execute("UPDATE users SET username = ? WHERE id = ?", username, user["id"])
        db.execute("UPDATE settings SET setting_value = ? WHERE user_id = ? AND setting_name = ?", darkmode, user["id"], "darkmode")
        db.execute("UPDATE settings SET setting_value = ? WHERE user_id = ? AND setting_name = ?", timezone, user["id"], "timezone")

        session["darkmode"] = darkmode
        session["timezone"] = timezone

        return redirect("/profile")

    else:

        settings_rows = db.execute("SELECT * FROM settings WHERE user_id = ?", session["user_id"])
        settings = {row["setting_name"]: row["setting_value"] for row in settings_rows}

        timezones = pytz.all_timezones
        update_settings()
        return render_template("profile.html", user=user, settings=settings, timezones=timezones)


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validet user input
        if not username:
            return apology("Missing username", 403)
        if not password:
            return apology("Missing password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) == 0:
            return apology("Invalid username and/or password", 403)

        user = rows[0]
        if not check_password_hash(user["hash"], password):
            return apology("Invalid username and/or password", 403)

        session["user_id"] = user["id"]

        update_settings()

        return redirect("/")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_repeat = request.form.get("password-repeat")

        # Validet user input
        if not username:
            return apology("Missing username", 400)
        if not password or not password_repeat:
            return apology("Missing password", 400)
        if password != password_repeat:
            return apology("Password does not match", 400)

        # Check is username is free
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 0:
            return apology("Username is taken", 400)

        # Insert user
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   username, hash)
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        user = rows[0]
        session["user_id"] = user["id"]

        # Add user settings
        for setting in settings:
            insert_settings(db, user["id"], setting, settings[setting])

        update_settings()

        flash("Registerd!")
        return redirect("/")
    else:
        return render_template("register.html")


def update_settings():
    if not session.get("user_id"):
        return
    settings_rows = db.execute("SELECT * FROM settings WHERE user_id = ?", session["user_id"])
    settings = {row["setting_name"]: row["setting_value"] for row in settings_rows}

    session["darkmode"] = settings["darkmode"]
    session["timezone"] = settings["timezone"]


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
