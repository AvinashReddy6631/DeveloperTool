import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    connection = psycopg2.connect(
        host="localhost",
        database="company_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        port=5432
    )

    print("PostgreSQL connected successfully!")

    connection.close()

except Exception as e:
    print("PostgreSQL connection failed:")
    print(e)