from flask import flash, redirect, render_template, session
import requests
from functools import wraps
import datetime
import pytz
from cs50 import SQL

BASE_API_URL = "https://world.openfoodfacts.net/api/v3/"
ENDING_API_URL = "?fields=product_name,nutriscore_data,nutriments,nutrition_grades,nutriscore_score"

db = SQL("sqlite:///data.db")


class ErrorResponse:
    def __init__(self, status=None, message=None):
        self.status = status
        self.message = message


class BarcodeRequest:
    def __init__(self):
        self.data = {}
        self.has_error = False
        self.error = ErrorResponse()


def get_product_url_barcode(barcode):
    return BASE_API_URL + "product/" + barcode + ENDING_API_URL


def get_product(barcode):
    """
    Takes the barcode and first checks if the barcode exists in the local db,
    if not it will check if the barcode exists in the API, if not then ERROR
    """
    product = BarcodeRequest()
    rows = db.execute("SELECT * FROM products WHERE id = ?", barcode)
    if len(rows) == 0:
        # Barcode did not exist grab it and add to local db
        print(f"Searching for {barcode} online")
        response = fetch_barcode(barcode)

        if response.status_code != 200:
            product.has_error = True
            product.error.status = response.status_code
            product.error.message = "Could not find product"
            return product
        data = process_data(response.json())

        if not validate_data(data):
            product.has_error = True
            product.error.status = 403
            product.error.message = "Product is missing data"
            return product

        insert_product(db, data)
    else:
        # barcode exits
        print(f"Found {barcode} localy")
    rows = db.execute("SELECT * FROM products WHERE id = ?", barcode)
    if len(rows) > 0:
        product.data = rows[0]
    else:
        product.has_error = True
        product.error.status = 404
        product.error.message = "Product not found in local database after insert."
    return product


def get_product_url_name(name):
    name = name.replace(" ", "%20")
    return BASE_API_URL + "search?search_terms=" + name


def process_data(json):
    data = {}
    # Get the name
    product = json["product"]
    data["id"] = json["code"]
    data["name"] = product.get("product_name")

    data["grade"] = product.get("nutrition_grades")
    data["score"] = product.get("nutriscore_score")
    # data["keywords"] = product.get("_keywords")

    # Nutriments
    data["kcal_100g"] = product.get("nutriments").get("energy-kcal_100g")
    data["fat_100g"] = product.get("nutriments").get("fat_100g")
    data["proteins_100g"] = product.get("nutriments").get("proteins_100g")
    data["salt_100g"] = product.get("nutriments").get("salt_100g")
    data["sugars_100g"] = product.get("nutriments").get("sugars_100g")
    data["sodium_100g"] = product.get("nutriments").get("sodium_100g")
    return data


def validate_data(data):
    if not data.get("name"):
        return False
    print(data.get("name"))
    print("Validating data")
    if not data.get("id"):
        return False
    if not data.get("grade"):
        return False

    for i in data:
        if not data[i]:
            print(f"Missing: {i}")
            data[i] = 0
    return True


def insert_product(db, data):
    db.execute("INSERT INTO products (id, name, grade, score, kcal_100g, fat_100g, proteins_100g, salt_100g, sugars_100g, sodium_100g) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
               data['id'], data['name'], data['grade'], data['score'], data['kcal_100g'], data['fat_100g'], data['proteins_100g'], data['salt_100g'], data['sugars_100g'], data['sodium_100g'])


def insert_search(db, user_id, product_id):
    db.execute(
        "INSERT INTO user_searches (user_id, product_id) VALUES (?, ?)", user_id, product_id)


def insert_settings(db, user_id, setting_name, setting_value):
    db.execute("INSERT INTO settings (user_id, setting_name, setting_value) VALUES (?, ?, ?)",
               user_id, setting_name, setting_value)


def insert_user_product(db, user_id, product_id):
    db.execute(
        "INSERT INTO user_products (user_id, product_id) VALUES (?, ?)", user_id, product_id)


def insert_new_list(db, user_id):
    list_id = db.execute(
        "INSERT INTO shopping_lists (user_id) VALUES (?)", user_id)
    return list_id


def fetch_barcode(barcode):
    return requests.get(get_product_url_barcode(barcode))


def fetch_name(name):
    return requests.get(get_product_url_name(name))


def apology(message, status_code):
    return render_template("error.html", top=status_code,
                           bottom=escape(message)), status_code


def apology_error(error):
    return render_template("error.html", top=error.status,
                           bottom=escape(error.message)), error.status


def fix_time(time_stamp, time_zone):
    format = "%Y-%m-%d %H:%M:%S %z"
    dt = datetime.datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S")
    tz = pytz.timezone(time_zone)
    dt = tz.localize(dt)
    dt = dt.astimezone(tz)

    return dt.strftime(format)


def sort_by_search_time(entry):
    format = "%Y-%m-%d %H:%M:%S %z"
    return datetime.datetime.strptime(entry["search_time"], format)


def escape(s):
    for old, new in [
        ("-", "--"),
        (" ", "-"),
        ("_", "__"),
        ("?", "~q"),
        ("%", "~p"),
        ("#", "~h"),
        ("/", "~s"),
        ('"', "''"),
    ]:
        s = s.replace(old, new)
        return s


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("You need to login to do that")
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def get_saved(user_id):
    return db.execute("SELECT DISTINCT p.id, p.name FROM products p JOIN (SELECT product_id FROM user_searches WHERE user_id = ? UNION SELECT product_id FROM user_products WHERE user_id = ?) combined ON p.id = combined.product_id", user_id, user_id)

