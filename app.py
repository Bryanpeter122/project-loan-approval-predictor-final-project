from flask import Flask, render_template, request
import pickle
import mysql.connector

# Database credentials
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''  # 🔁 Change this
DB_NAME = 'housing_db'
TABLE_NAME = 'predictions'

# Load model
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

# Create Flask app
app = Flask(__name__)

# Check/create DB and table on startup
def initialize_database():
    # Connect to MySQL (not a specific DB yet)
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    # Create DB if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()

    # Reconnect to the created DB
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            area INT,
            bedrooms INT,
            bathrooms INT,
            stories INT,
            parking INT,
            predicted_price FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Call initialization on startup
initialize_database()

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None

    if request.method == 'POST':
        try:
            # Get inputs
            area = int(request.form['area'])
            bedrooms = int(request.form['bedrooms'])
            bathrooms = int(request.form['bathrooms'])
            stories = int(request.form['stories'])
            parking = int(request.form['parking'])

            # Predict
            input_data = [[area, bedrooms, bathrooms, stories, parking]]
            predicted_price = float(model.predict(input_data)[0])  # ensure native float
            prediction = f"₱{predicted_price:,.2f}"

            # Save to DB
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (area, bedrooms, bathrooms, stories, parking, predicted_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (area, bedrooms, bathrooms, stories, parking, predicted_price))
            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            prediction = f"Error: {e}"

    return render_template('index.html', prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)
