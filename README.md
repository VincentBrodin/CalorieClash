# CalorieClash

#### Video Demo: [Watch Here](https://youtu.be/tacyYy510rA)

## Description

**CalorieClash** is a web application designed to help users save, search, and compare food products. Built using Flask with JavaScript, Python, HTML, CSS, and SQL, the application allows users to rate food items, create shopping lists, and even scan barcodes using their devices. The goal is to provide an easy and interactive way to manage nutritional information and track favorite foods.

### Key Features
- **Search Products**: Enter a barcode or scan it to retrieve product details.
- **Compare Products**: Compare two food products based on nutritional values.
- **Rate and Save**: Rate the foods you like or dislike and save them for future reference.
- **Shopping Lists**: Create and manage personalized shopping lists.
- **User Accounts**: Manage your profile settings, search history, and saved products.

## Resources
- Data Source: [Open Food Facts](https://world.openfoodfacts.org/)
- Barcode Scanning: [html5-qrcode](https://unpkg.com/browse/html5-qrcode@2.0.9/)

---

## Templates Overview

### compare.html
Compares two food products based on their barcodes and highlights differences in green, red, or white, depending on which product has better nutritional values.

### debug.html
Displays all food products for debugging purposes.

### error.html
Shows an error message with the associated error code.

### history.html
Displays the user’s search history, showing what they searched for and when. Users can also clear their search history.

### index.html
Prompts users to enter or scan a barcode to search for a product or compare two products.

### layout.html
Defines the general layout of the website, including the navigation bar and footer.

### list.html
Shows the user's current shopping list, allowing edits to items.

### lists.html
Displays all of the user's shopping lists, allowing them to add or remove lists.

### login.html
A simple login form for user authentication.

### product.html
Displays detailed nutritional information about a specific food product.

### profile.html
Allows users to edit their profile information, including username, timezone, and theme preferences (light/dark mode).

### register.html
A simple registration form for creating a new user account.

### saved.html
Displays the user’s saved products and allows them to remove items.

---

## Python Files Overview

### app.py
Handles all the routes for the web application, including user interactions, barcode searches, and product comparisons.

### helper.py
A utility module providing various functions and classes for managing food products, barcodes, and user interactions.

#### Key Functions:
1. **Error Handling**
   - `ErrorResponse`: Structures error messages with a status and message.
   - `BarcodeRequest`: Manages barcode data requests and related errors.

2. **Product Management**
   - `get_product(barcode)`: Fetches product details from the local database or an external API if not found locally.
   - `process_data(json)`: Extracts and formats nutritional information from the API response.
   - `validate_data(data)`: Ensures fetched data contains all required fields; fills missing values with defaults.
   - `insert_product(db, data)`: Inserts a product into the local database.

3. **User Interactions**
   - `insert_search(db, user_id, product_id)`: Logs product searches by users.
   - `insert_user_product(db, user_id, product_id)`: Saves a product for a user.
   - `insert_new_list(db, user_id)`: Creates a new shopping list for the user.

4. **API Requests**
   - `fetch_barcode(barcode)`: Fetches product details from the API based on a barcode.
   - `fetch_name(name)`: Fetches product details based on a product's name.

5. **Utility Functions**
   - `fix_time(time_stamp, time_zone)`: Adjusts and formats timestamps for the user’s timezone.
   - `sort_by_search_time(entry)`: Sorts entries by their search timestamp.
   - `escape(s)`: Escapes special characters for safe HTML display.

6. **Error Rendering**
   - `apology(message, status_code)`: Displays a custom error page.
   - `apology_error(error)`: Renders an error page using an `ErrorResponse`.

7. **User Authentication**
   - `login_required(f)`: Decorator function ensuring users are logged in before accessing specific pages.

8. **Fetching Saved Products**
   - `get_saved(user_id)`: Retrieves the user’s saved products based on their search history.

---

## Database Structure

### Tables

#### `users`
Stores user account data.
- **id**: Primary key, auto-incremented.
- **username**: Unique identifier for the user.
- **hash**: Hashed password.

#### `products`
Stores detailed information about products, including nutritional data.
- **id**: Primary key.
- **name**: Name of the product.
- **grade**, **score**: Quality and health indicators.
- **kcal_100g**, **fat_100g**, **proteins_100g**, **salt_100g**, **sugars_100g**, **sodium_100g**: Nutritional values per 100g.

#### `user_products`
Many-to-many relationship table linking users to products they have saved.

#### `user_searches`
Logs each product search performed by users, along with a timestamp.

#### `settings`
Stores user preferences such as timezone and theme (light/dark mode).

#### `shopping_lists` and `shopping_list_items`
Handles user-generated shopping lists, including the items within each list.

#### `product_ratings`
Stores user ratings and comments for products.
- **rating**: Integer rating from 0 to 5.
- **has_comment**: Boolean indicating if a comment is attached.

---

## Relationships
- **Users & Products**: Linked through a many-to-many relationship via `user_products`.
- **Search Logs**: Logged in the `user_searches` table.
- **Shopping Lists**: Managed through the `shopping_lists` and `shopping_list_items` tables.
- **User Settings**: Stored in the `settings` table, allowing customization of profile preferences.
