
import psycopg2
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()




DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", 5432))
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(100) NOT NULL,
            salary INTEGER NOT NULL
        )
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Employees table created successfully!")


def insert_employees():
    connection = get_connection()
    cursor = connection.cursor()

    employees = [
        ("Avinash", "AI Engineer", 80000),
        ("Rahul", "Backend Developer", 70000),
        ("Priya", "ML Engineer", 85000),
        ("Arjun", "Frontend Developer", 65000)
    ]

    cursor.executemany("""
        INSERT INTO employees (name, role, salary)
        VALUES (%s, %s, %s)
    """, employees)

    connection.commit()

    cursor.close()
    connection.close()

    print("Employees inserted successfully!")


if __name__ == "__main__":
    init_database()
    insert_employees()