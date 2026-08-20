import os

import psycopg2
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", "5432")),
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(100) NOT NULL,
            salary INTEGER NOT NULL,
            company VARCHAR(100) NOT NULL
        )
        """
    )

    connection.commit()

    cursor.close()
    connection.close()

    print("Employees table created successfully!")


# ============================================================
# INSERT TEST / SEED DATA
# ============================================================

def insert_employees():

    connection = get_connection()
    cursor = connection.cursor()

    employees = [
        ("Avinash", "AI Engineer", 80000, "Google"),
        ("Rahul", "Backend Developer", 70000, "Google"),
        ("Priya", "ML Engineer", 85000, "Google"),
        ("Arjun", "Frontend Developer", 65000, "Google"),
    ]

    cursor.executemany(
        """
        INSERT INTO employees
            (name, role, salary, company)
        VALUES
            (%s, %s, %s, %s)
        """,
        employees,
    )

    connection.commit()

    cursor.close()
    connection.close()

    print("Employees inserted successfully!")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    init_database()

    insert_employees()