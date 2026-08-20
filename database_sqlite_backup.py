import sqlite3


def init_database():
    conn = sqlite3.connect("company.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            salary INTEGER
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM employees")

    count = cursor.fetchone()[0]

    if count == 0:
        employees = [
    {
        "id": 1,
        "name": "Avinash",
        "role": "AI Engineer",
        "salary": 80000,
        "company": "Google"
    },
    {
        "id": 2,
        "name": "Rahul",
        "role": "Backend Developer",
        "salary": 70000,
        "company": "Microsoft"
    },
    {
        "id": 3,
        "name": "Priya",
        "role": "ML Engineer",
        "salary": 85000,
        "company": "Google"
    },
    {
        "id": 4,
        "name": "Arjun",
        "role": "Frontend Developer",
        "salary": 65000,
        "company": "Amazon"
    }
]

        cursor.executemany("""
            INSERT INTO employees (name, role, salary)
            VALUES (?, ?, ?)
        """, employees)

    conn.commit()
    conn.close()


def get_employees():
    conn = sqlite3.connect("company.db")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
    """)

    employees = cursor.fetchall()

    conn.close()

    return employees

def find_employee(name):
    conn = sqlite3.connect("company.db")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        WHERE name LIKE ?
    """, (f"%{name}%",))

    employees = cursor.fetchall()

    conn.close()

    return employees
def find_employees_by_salary(min_salary):
    conn = sqlite3.connect("company.db")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        WHERE salary > ?
        ORDER BY salary DESC
    """, (min_salary,))

    employees = cursor.fetchall()

    conn.close()

    return employees


def get_highest_paid_employee():
    conn = sqlite3.connect("company.db")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        ORDER BY salary DESC
        LIMIT 1
    """)

    employee = cursor.fetchone()

    conn.close()

    return employee


def search_company(query):
    conn = sqlite3.connect("company.db")

    cursor = conn.cursor()

    query = query.lower()

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        WHERE LOWER(name) LIKE ?
           OR LOWER(role) LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    employees = cursor.fetchall()

    conn.close()

    return employees


def get_employees_paginated(page=1, page_size=2):
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()

    offset = (page - 1) * page_size

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        ORDER BY id
        LIMIT ? OFFSET ?
    """, (page_size, offset))

    employees = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]

    conn.close()

    total_pages = (total + page_size - 1) // page_size

    return employees, total, total_pages




def filter_employees(
    role=None,
    min_salary=None,
    max_salary=None,
    page=1,
    page_size=10
):
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()

    conditions = []
    parameters = []

    # Role filter
    if role:
        conditions.append("LOWER(role) LIKE ?")
        parameters.append(f"%{role.lower()}%")

    # Minimum salary
    if min_salary is not None:
        conditions.append("salary >= ?")
        parameters.append(min_salary)

    # Maximum salary
    if max_salary is not None:
        conditions.append("salary <= ?")
        parameters.append(max_salary)

    # Build WHERE clause
    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Count matching employees
    count_query = f"""
        SELECT COUNT(*)
        FROM employees
        {where_clause}
    """

    cursor.execute(count_query, parameters)

    total = cursor.fetchone()[0]

    # Pagination
    offset = (page - 1) * page_size

    query = f"""
        SELECT id, name, role, salary
        FROM employees
        {where_clause}
        ORDER BY salary DESC
        LIMIT ? OFFSET ?
    """

    cursor.execute(
        query,
        parameters + [page_size, offset]
    )

    employees = cursor.fetchall()

    conn.close()

    total_pages = (total + page_size - 1) // page_size

    return employees, total, total_pages

if __name__ == "__main__":
    init_database()

    print("Database initialized!")
    print(get_employees())