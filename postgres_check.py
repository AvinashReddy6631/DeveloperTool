import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


connection = psycopg2.connect(
    host="localhost",
    database="company_db",
    user="postgres",
    password=os.getenv("DB_PASSWORD"),
    port=5432
)

cursor = connection.cursor()

cursor.execute("""
    SELECT id, name, role, salary
    FROM employees
    ORDER BY id
""")

employees = cursor.fetchall()

print("\nEmployees in PostgreSQL:\n")

for employee in employees:
    print(employee)

cursor.close()
connection.close()