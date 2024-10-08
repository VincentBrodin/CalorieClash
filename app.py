from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
import pytz

from helper import (
    apology, fix_time, login_required, insert_search, insert_settings,
    sort_by_search_time, insert_user_product, insert_new_list, get_product,
    apology_error, get_saved
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
        saved = get_saved(session["user_id"])
    return render_template("index.html", saved=saved)


@app.route("/update_list_count", methods=["POST"])
def update_list_count():
    count = request.json.get("count", 0)
    list_id = request.json.get("list_id")
    product_id = request.json.get("product_id")

    if not count or not list_id or not product_id:
        return "BAD", 403

    rows = db.execute("SELECT * FROM shopping_list_items WHERE shopping_list_id = ? AND product_id = ?",
                      list_id, product_id)
    if len(rows) == 0:
        return "Does not exist", 404

    rows = db.execute("SELECT * FROM shopping_lists WHERE user_id = ? AND id = ?",
                      session["user_id"], list_id)
    if len(rows) == 0:
        return "Not your list", 403

    if int(count) <= 0:
        print("Count is zero or less removing item")
        db.execute("DELETE FROM shopping_list_items WHERE shopping_list_id = ? AND product_id = ?",
                   list_id, product_id)
        return "Remove", 200
    else:
        print(f"Changing count to {count}")
        db.execute("UPDATE shopping_list_items SET count = ? WHERE shopping_list_id = ? AND product_id = ?",
                   count, list_id, product_id)
    return "Good", 200


@app.route("/search_barcode", methods=["GET"])
def search_barcode():
    barcode = request.args.get("barcode")
    if not barcode:
        return apology("Missing barcode", 403)

    product = get_product(barcode)

    if product.has_error:
        return apology_error(product.error)

    is_saved = False
    if session.get("user_id"):
        # Add search to history
        insert_search(db, session["user_id"], barcode)
        print("User id found :)")

        # Check if the user has saved this product
        saved = db.execute(
            "SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], barcode)
        is_saved = len(saved) != 0
        print("Saving search")
    else:
        print("No user id")
    comments = db.execute(
        "SELECT * FROM product_ratings WHERE product_id = ? ORDER BY id DESC", barcode)

    average_rating = 0
    if comments:
        for comment in comments:
            average_rating += comment.get("rating")
        average_rating /= len(comments)
        round(average_rating, 1)
    else:
        average_rating = 0

    update_settings()
    return render_template("product.html", data=product.data, is_saved=is_saved, comments=comments, average_rating=average_rating)


@app.route("/submit_rating", methods=["POST"])
@login_required
def submit_rating():
    product_id = request.form.get("product_id")
    rating = request.form.get("rating")
    comment = request.form.get("comment")

    if not product_id:
        return apology("Missing product id", 403)

    if not rating:
        return apology("Missing rating", 403)

    try:
        rating = int(rating)
    except ValueError:
        return apology("Rating is not an integer", 403)

    if 0 > rating or rating > 5:
        return apology("Rating is not 0-5", 403)

    has_comment = comment != ""
    user_id = session["user_id"]

    db.execute("INSERT INTO product_ratings (user_id, product_id, rating, has_comment, comment) VALUES (?, ?, ?, ?, ?)",
               user_id, product_id, rating, has_comment, comment)
    return redirect(f"/search_barcode?barcode={product_id}")


@app.route("/compare_products", methods=["GET"])
def compare_products():
    # ---Barcode a---
    barcode_a = request.args.get("barcode_a")
    if not barcode_a:
        return apology("Missing barcode a", 403)

    product_a = get_product(barcode_a)
    if product_a.has_error:
        return apology_error(product_a.error)

    is_saved_a = False
    if session.get("user_id"):
        insert_search(db, session["user_id"], barcode_a)
        saved = db.execute(
            "SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], barcode_a)
        is_saved_a = len(saved) != 0

    # ---Barcode b---
    barcode_b = request.args.get("barcode_b")
    if not barcode_b:
        return apology("Missing barcode b", 403)

    product_b = get_product(barcode_b)
    if product_b.has_error:
        return apology_error(product_b.error)

    is_saved_b = False
    if session.get("user_id"):
        insert_search(db, session["user_id"], barcode_b)
        saved = db.execute(
            "SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], barcode_b)
        is_saved_b = len(saved) != 0

    # ---return information---
    update_settings()
    return render_template("compare.html", data_a=product_a.data, is_saved_a=is_saved_a, data_b=product_b.data, is_saved_b=is_saved_b)


@app.route("/lists")
@login_required
def shopping_lists():
    lists = db.execute(
        "SELECT * FROM shopping_lists WHERE user_id = ?", session["user_id"])
    return render_template("lists.html", lists=lists)


@app.route("/list", methods=["GET"])
def shopping_list():
    list_id = request.args.get("id")
    if not list_id:
        return apology("Missing list id", 400)
    rows = db.execute("SELECT * FROM shopping_lists WHERE id = ?", list_id)
    if len(rows) == 0:
        return apology("Shopping list does not exist", 404)
    shopping_list = rows[0]
    products = db.execute(
        "SELECT * FROM shopping_list_items, products WHERE shopping_list_items.product_id = products.id AND shopping_list_id = ?", list_id)

    saved = []
    if session.get("user_id"):
        saved = get_saved(session["user_id"])

    return render_template("list.html", shopping_list=shopping_list, products=products, saved=saved)

# Grab all users saved products to show as autocomplete
@app.route("/add_product_to_list", methods=["POST"])
@login_required
def add_product_to_list():
    list_id = request.form.get("id")
    barcode = request.form.get("product_id")

    if not list_id:
        return apology("Missing list id", 400)

    if not barcode:
        return apology("Missing product id", 400)

    rows = db.execute("SELECT * FROM shopping_lists WHERE id = ?", list_id)
    if len(rows) == 0:
        return apology("Shopping list does not exist", 404)
    shopping_list = rows[0]

    if shopping_list["user_id"] != session["user_id"]:
        return apology("You don't own this list", 403)

    product = get_product(barcode)

    if product.has_error:
        return apology_error(product.error)

    rows = db.execute(
        "SELECT * FROM shopping_list_items WHERE shopping_list_id = ? AND product_id = ?", list_id, barcode)
    if len(rows) != 0:
        count = rows[0].get("count")
        count += 1
        db.execute("UPDATE shopping_list_items SET count = ? WHERE shopping_list_id = ? AND product_id = ?",
                   count, list_id, barcode)
    else:
        place = len(db.execute(
            "SELECT * FROM shopping_list_items WHERE shopping_list_id = ?", list_id))
        db.execute("INSERT INTO shopping_list_items (shopping_list_id, product_id, count, place) VALUES (?, ?, ?, ?)",
                   list_id, barcode, 1, place)

    flash("Added!")
    return redirect(f"/list?id={list_id}")


@app.route("/remove_list", methods=["POST"])
@login_required
def remove_list():
    list_id = request.form.get("id")
    if not list_id:
        return apology("Missing list id", 400)
    rows = db.execute("SELECT * FROM shopping_lists WHERE id = ?", list_id)
    if len(rows) == 0:
        return apology("Shopping list does not exist", 404)
    shopping_list = rows[0]

    if shopping_list["user_id"] != session["user_id"]:
        return apology("You don't own this list", 403)
    db.execute(
        "DELETE FROM shopping_list_items WHERE shopping_list_id = ?", list_id)
    db.execute("DELETE FROM shopping_lists WHERE id = ?", list_id)

    flash("Removed!")
    return redirect("/lists")


@app.route("/add_new_list", methods=["POST"])
@login_required
def new_shopping_list():
    # TODO: Add a new list to the db and redirect user to the new list
    list_id = insert_new_list(db, session["user_id"])
    return redirect(f"/list?id={list_id}")


@app.route("/update_list_name", methods=["POST"])
@login_required
def update_list_name():
    list_id = request.form.get("id")
    new_list_name = request.form.get("name")

    if not list_id:
        return apology("Missing list id", 400)

    if not new_list_name:
        return apology("Missing new list name", 400)

    rows = db.execute("SELECT * FROM shopping_lists WHERE id = ?", list_id)

    if len(rows) == 0:
        return apology("List does not exsits", 404)

    shopping_list = rows[0]

    if shopping_list["user_id"] != session["user_id"]:
        return apology("You don't own this list", 400)

    db.execute("UPDATE shopping_lists SET name = ? WHERE id = ?",
               new_list_name, list_id)

    flash("Name updated")
    return redirect(f"/list?id={list_id}")


@app.route("/history", methods=["GET"])
@login_required
def history():
    history = db.execute(
        "SELECT * FROM user_searches, products WHERE user_id = ? AND product_id = products.id", session["user_id"])
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
    db.execute("DELETE FROM user_searches WHERE user_id = ?",
               session["user_id"])
    return redirect("/history")


@app.route("/save", methods=["POST"])
@login_required
def save():
    product_id = request.form.get("id")
    if not product_id:
        return apology("Missing product id", 403)
    rows = db.execute(
        "SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], product_id)
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
    rows = db.execute(
        "SELECT * FROM user_products WHERE user_id = ? AND product_id = ?", session["user_id"], product_id)
    if len(rows) == 0:
        return redirect("/saved")
    db.execute("DELETE FROM user_products WHERE user_id = ? AND product_id = ?",
               session["user_id"], product_id)
    flash("Removed!")
    return redirect("/saved")


@app.route("/saved", methods=["GET"])
@login_required
def saved():
    saved = db.execute(
        "SELECT * FROM user_products, products WHERE products.id = product_id AND user_id = ?", session["user_id"])
    return render_template("saved.html", saved=saved)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_rows = db.execute(
        "SELECT * FROM users WHERE id = ?", session["user_id"])
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

        db.execute("UPDATE users SET username = ? WHERE id = ?",
                   username, user["id"])
        db.execute("UPDATE settings SET setting_value = ? WHERE user_id = ? AND setting_name = ?",
                   darkmode, user["id"], "darkmode")
        db.execute("UPDATE settings SET setting_value = ? WHERE user_id = ? AND setting_name = ?",
                   timezone, user["id"], "timezone")

        session["darkmode"] = darkmode
        session["timezone"] = timezone

        return redirect("/profile")

    else:

        settings_rows = db.execute(
            "SELECT * FROM settings WHERE user_id = ?", session["user_id"])
        settings = {row["setting_name"]: row["setting_value"]
                    for row in settings_rows}

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
    """
    Makes sure that the users has the latest settings.
    """
    if not session.get("user_id"):
        return
    settings_rows = db.execute(
        "SELECT * FROM settings WHERE user_id = ?", session["user_id"])
    settings = {row["setting_name"]: row["setting_value"]
                for row in settings_rows}

    session["darkmode"] = settings["darkmode"]
    session["timezone"] = settings["timezone"]


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
