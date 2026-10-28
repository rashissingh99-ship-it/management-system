import os
import hashlib
import mysql.connector as m


# ------------------ Utilities ------------------
def get_db_connection():
    """Return a new DB connection, or None if it fails.
    Set the password in an environment variable instead of hardcoding it:
        Windows:   setx DB_PASSWORD "yourpassword"
        Linux/Mac: export DB_PASSWORD="yourpassword"
    """
    try:
        return m.connect(
            host="localhost",
            user="root",
            password=os.getenv("DB_PASSWORD", ""),
            database="e_commerce",
        )
    except m.Error as err:
        print(f"Error connecting to database: {err}")
        return None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def read_int(prompt):
    """Keep asking until the user enters a whole number."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print('Please enter a valid number.')


def line():
    print('----------------------------------------------------------------')


# ------------------ Welcome ------------------
def welcome():
    while True:
        line()
        print('--------------------------Namaste-----------------------------')
        print('************************* Welcome to Blueberry ************************')
        line()
        print('What is your role:')
        print('Press 1 for SELLER')
        print('Press 2 for CUSTOMER')
        print('Press 3 to EXIT')

        role = read_int('Enter 1, 2 or 3: ')

        if role == 1:
            scheck()
        elif role == 2:
            customer_id = identity()
            if customer_id is not None:
                menu(customer_id)
        elif role == 3:
            print('THANK YOU FOR USING BLUEBERRY')
            return
        else:
            print('Please enter valid input.')


# ------------------ Customer Functions ------------------
def identity():
    """Returns the logged-in customer's ID, or None."""
    while True:
        line()
        print('Press 1 if already a user')
        print('Press 2 to create a new account')
        print('Press 3 to go back')

        choice = read_int('Enter 1, 2 or 3: ')

        if choice == 1:
            customer_id = login()
            if customer_id is not None:
                return customer_id
        elif choice == 2:
            customer_id = create()
            if customer_id is not None:
                return customer_id
        elif choice == 3:
            return None
        else:
            print('Invalid input.')


def create():
    """Creates a new account. Returns the new Customer_ID, or None."""
    line()

    while True:
        name = input('Enter your full name: ').strip()
        if name and name.replace(' ', '').isalpha():
            break
        print('Please enter valid name.')

    db = get_db_connection()
    if db is None:
        return None
    co = db.cursor()

    try:
        while True:
            username = input('Enter username: ').strip()
            if not username:
                print('Username cannot be empty.')
                continue
            co.execute('SELECT 1 FROM Customers WHERE Username=%s', (username,))
            if co.fetchone():
                print('Username already taken. Try another.')
                continue
            break

        while True:
            password = input('Enter password (min 6 characters): ')
            if len(password) >= 6:
                break
            print('Password too short.')

        address = input('Enter address: ').strip()

        while True:
            phone = input('Enter phone number (10 digits): ').strip()
            if phone.isdigit() and len(phone) == 10:
                break
            print('Please enter valid phone number.')

        while True:
            email = input('Enter email: ').strip()
            if '@' in email and '.' in email.split('@')[-1]:
                break
            print('Please enter valid email.')

        co.execute('SELECT MAX(Customer_ID) FROM Customers')
        last_id = co.fetchone()[0]
        new_id = 1 if last_id is None else int(last_id) + 1

        co.execute(
            'INSERT INTO Customers VALUES (%s,%s,%s,%s,%s,%s,%s)',
            (new_id, username, hash_password(password), name, address, phone, email),
        )
        db.commit()

        print('Account successfully created! Your Customer ID is:', new_id)
        return new_id

    except m.Error as err:
        db.rollback()
        print(f'Could not create account: {err}')
        return None
    finally:
        co.close()
        db.close()


def login():
    """Returns Customer_ID on success, or None after 3 failed attempts."""
    db = get_db_connection()
    if db is None:
        return None
    co = db.cursor()

    try:
        for attempt in range(3):
            line()
            username = input('Enter username: ').strip()
            password = input('Enter password: ')

            co.execute(
                'SELECT Customer_ID, Name FROM Customers '
                'WHERE Username=%s AND Password_Hash=%s',
                (username, hash_password(password)),
            )
            user = co.fetchone()

            if user:
                print(f'Welcome, {user[1]}!')
                return user[0]
            print(f'Invalid username or password. Attempts left: {2 - attempt}')

        print('Too many failed attempts.')
        return None
    except m.Error as err:
        print(f'Database error: {err}')
        return None
    finally:
        co.close()
        db.close()


def menu(customer_id):
    while True:
        line()
        print('***************************** MENU *****************************')
        print('1: Search Products')
        print('2: View Purchase History')
        print('3: Place Order')
        print('4: Return Product')
        print('5: Cancel Order')
        print('6: Give Feedback')
        print('7: Logout')

        choice = read_int('Enter your choice: ')

        if choice == 1:
            search()
        elif choice == 2:
            purchase_history(customer_id)
        elif choice == 3:
            order(customer_id)
        elif choice == 4:
            product_return(customer_id)
        elif choice == 5:
            cancel_order(customer_id)
        elif choice == 6:
            feedback(customer_id)
        elif choice == 7:
            print('Logged out.')
            return
        else:
            print('Invalid input.')


# ------------------ Product Search ------------------
def print_products(products):
    for idx, prod in enumerate(products, start=1):
        line()
        print(f'PRODUCT NUMBER {idx}')
        print(f'Product ID: {prod[0]}')
        print(f'Category: {prod[1]}')
        print(f'Name: {prod[2]}')
        print(f'Quantity available: {prod[3]}')
        print(f'Price: {prod[4]}')
        print(f'Brand Name: {prod[5]}')
        print(f'Seller ID: {prod[6]}')
        line()


def search():
    while True:
        line()
        print('Press 1: Search by Category')
        print('Press 2: Search by Brand')
        print('Press 3: View All Products')
        print('Press 4: Go Back to Menu')

        choice = read_int('Enter your choice: ')

        if choice == 1:
            category()
        elif choice == 2:
            brand()
        elif choice == 3:
            all_products()
        elif choice == 4:
            return
        else:
            print('Invalid input.')


def category():
    db = get_db_connection()
    if db is None:
        return
    co = db.cursor()

    try:
        co.execute('SELECT DISTINCT Category FROM Products')
        print('Available categories:')
        for cat in co.fetchall():
            print(cat[0])

        cat_input = input('Enter category to search: ').strip()
        co.execute('SELECT * FROM Products WHERE Category LIKE %s',
                   ('%' + cat_input + '%',))
        results = co.fetchall()

        if not results:
            print('No products found in this category.')
        else:
            print_products(results)
    except m.Error as err:
        print(f'Database error: {err}')
    finally:
        co.close()
        db.close()


def brand():
    db = get_db_connection()
    if db is None:
        return
    co = db.cursor()

    try:
        co.execute('SELECT DISTINCT Brand_Name FROM Products')
        print('Available brands:')
        for b in co.fetchall():
            print(b[0])

        brand_input = input('Enter brand to search: ').strip()
        co.execute('SELECT * FROM Products WHERE Brand_Name LIKE %s',
                   ('%' + brand_input + '%',))
        results = co.fetchall()

        if not results:
            print('No products found for this brand.')
        else:
            print_products(results)
    except m.Error as err:
        print(f'Database error: {err}')
    finally:
        co.close()
        db.close()


def all_products():
    db = get_db_connection()
    if db is None:
        return
    co = db.cursor()

    try:
        co.execute('SELECT * FROM Products')
        products = co.fetchall()
        if not products:
            print('No products available.')
        else:
            print_products(products)
    except m.Error as err:
        print(f'Database error: {err}')
    finally:
        co.close()
        db.close()


# ------------------ Purchase History ------------------
def purchase_history(customer_id):
    db = get_db_connection()
    if db is None:
        return
    co = db.cursor()

    try:
        co.execute('SELECT * FROM Orders WHERE Customer_ID=%s', (customer_id,))
        orders = co.fetchall()

        if not orders:
            print('No orders found.')
            return

        for idx, o in enumerate(orders, start=1):
            line()
            print(f'ORDER NUMBER: {idx}')
            print(f'Transaction ID: {o[0]}')
            print(f'Product ID: {o[2]}')
            print(f'Date of dispatch: {o[3]}')
            print(f'Quantity: {o[4]}')
            print(f'Price: {o[5]}')
            print(f'Total Amount: {o[6]}')
            line()
    except m.Error as err:
        print(f'Database error: {err}')
    finally:
        co.close()
        db.close()


# ------------------ Placeholder Functions ------------------
def order(customer_id):
    print("Order functionality not implemented.")


def product_return(customer_id):
    print("Return functionality not implemented.")


def cancel_order(customer_id):
    print("Cancel functionality not implemented.")


def feedback(customer_id):
    print("Feedback functionality not implemented.")


def scheck():
    print("Seller functionality not implemented.")


# ------------------ Start Program ------------------
if __name__ == "__main__":
    welcome()
