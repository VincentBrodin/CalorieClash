# CalorieClash
#### Video Demo: <URL HERE>
#### Description:
Web application built with Flask (JS, Py, HTML, CSS, SQL)
This is my final project for CS50.

### Resources:
- https://world.openfoodfacts.org/
- https://unpkg.com/browse/html5-qrcode@2.0.9/ (Barcode scanner)

### Tables

#### 1. `users`
Stores user data.

- **id**: Primary key, auto-incremented.
- **username**: Unique username.
- **hash**: Password hash.

#### 2. `products`
Stores product details, including nutritional info.

- **id**: Primary key.
- **name**: Product name.
- **grade**, **score**: Quality indicators.
- **kcal_100g**, **fat_100g**, **proteins_100g**, **salt_100g**, **sugars_100g**, **sodium_100g**: Nutritional values per 100g.

#### 3. `user_products`
Many-to-many relationship between users and products.

#### 4. `user_searches`
Tracks product searches by users with a timestamp.

#### 5. `settings`
Stores key-value settings for each user.

#### 6. `shopping_lists` and `shopping_list_items`
Users can create shopping lists, and each list can have multiple items.

#### 7. `product_ratings`
Stores user ratings and comments for products.

- **rating**: Integer (0-5).
- **has_comment**: Indicates if a comment is present.

### Relationships
- Users and products: Many-to-many via `user_products`.
- Product searches: Logged in `user_searches`.
- Shopping lists: Managed via `shopping_lists` and `shopping_list_items`.
- User settings stored in `settings`.

