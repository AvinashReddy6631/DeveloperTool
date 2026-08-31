import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# PostgreSQL Configuration
# ============================================
def env_value(name, default=None):
    value = os.getenv(name, default)
    if value is None:
        return None
    return str(value).strip().strip('"').strip("'")


DB_CONFIG = {
    "host": env_value("DB_HOST"),
    "database": env_value("DB_NAME"),
    "user": env_value("DB_USER"),
    "password": env_value("DB_PASSWORD"),
    "port": int(env_value("DB_PORT", "5432"))
}


# ============================================
# Database Connection
# ============================================

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ============================================
# List All Employees
# ============================================

def list_employees():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        ORDER BY id
    """)

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    if not employees:
        return "No employees found."

    return "\n".join(
        f"ID: {employee[0]}, "
        f"Name: {employee[1]}, "
        f"Role: {employee[2]}, "
        f"Salary: {employee[3]}"
        for employee in employees
    )


# ============================================
# Search Employee By Name
# ============================================

def search_employee(name):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        WHERE name ILIKE %s
    """, (f"%{name}%",))

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    if not employees:
        return f"No employee found with name '{name}'."

    return "\n".join(
        f"ID: {employee[0]}, "
        f"Name: {employee[1]}, "
        f"Role: {employee[2]}, "
        f"Salary: {employee[3]}"
        for employee in employees
    )


# ============================================
# Employees Earning More Than
# ============================================

def employees_earning_more_than(min_salary):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name, role, salary
        FROM employees
        WHERE salary > %s
        ORDER BY salary DESC
    """, (min_salary,))

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    if not employees:
        return f"No employees earn more than {min_salary}."

    return "\n".join(
        f"Name: {employee[0]}, "
        f"Role: {employee[1]}, "
        f"Salary: {employee[2]}"
        for employee in employees
    )
def create_conversation_table():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                user_query TEXT NOT NULL,
                resolved_query TEXT,
                agent VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        connection.commit()

    finally:
        cursor.close()
        connection.close()

# ============================================
# Conversation Memory
# ============================================

def save_conversation(
    session_id,
    user_query,
    resolved_query,
    agent
):
    """Save one conversation turn in PostgreSQL."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO conversations (
                session_id,
                user_query,
                resolved_query,
                agent
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                session_id,
                user_query,
                resolved_query,
                agent
            )
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def get_conversation_history(
    session_id,
    limit=8
):
    """Return recent conversation turns for one session."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                user_query,
                resolved_query,
                agent
            FROM conversations
            WHERE session_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            (
                session_id,
                limit
            )
        )

        rows = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    # Query returns newest first. Reverse so the caller receives
    # chronological conversation order.
    rows.reverse()

    return rows


def get_recent_conversation_context(
    session_id,
    limit=8
):
    """Return recent conversation history as context text."""

    rows = get_conversation_history(
        session_id,
        limit
    )

    if not rows:
        return ""

    context_lines = []

    for user_query, resolved_query, agent in rows:

        context_lines.append(
            f"User: {user_query}"
        )

        if resolved_query:
            context_lines.append(
                f"Resolved: {resolved_query}"
            )

        if agent:
            context_lines.append(
                f"Agent: {agent}"
            )

    return "\n".join(context_lines)


def clear_conversation(session_id):
    """Delete all stored conversation history for one session."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM conversations
            WHERE session_id = %s
            """,
            (session_id,)
        )

        deleted_rows = cursor.rowcount

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return deleted_rows


# ============================================
# Highest Paid Employee
# ============================================

def highest_paid_employee():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name, role, salary
        FROM employees
        ORDER BY salary DESC
        LIMIT 1
    """)

    employee = cursor.fetchone()

    cursor.close()
    connection.close()

    if not employee:
        return "No employees found."

    return (
        f"Name: {employee[0]}, "
        f"Role: {employee[1]}, "
        f"Salary: {employee[2]}"
    )


# ============================================
# Company Search
# Searches Name OR Role
# ============================================
# ============================================
# Company Search
# Searches Company, Employee Name OR Role
# ============================================

def company_search(query):

    connection = get_connection()
    cursor = connection.cursor()

    query_clean = query.lower().strip()

    # General request for all companies
    if query_clean in [
        "companies",
        "company",
        "all companies",
        "list companies",
        "which companies",
        "what companies",
        "which companies are in the database"
    ]:

        cursor.execute("""
            SELECT DISTINCT company
            FROM employees
            WHERE company IS NOT NULL
            ORDER BY company
        """)

        companies = cursor.fetchall()

        cursor.close()
        connection.close()

        if not companies:
            return "No companies found."

        return "\n".join(
            company[0]
            for company in companies
        )

    # Search by company, employee name, or role
    cursor.execute("""
        SELECT id, name, role, salary, company
        FROM employees
        WHERE company ILIKE %s
           OR name ILIKE %s
           OR role ILIKE %s
        ORDER BY id
    """, (
        f"%{query}%",
        f"%{query}%",
        f"%{query}%"
    ))

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    if not employees:
        return f"No company or employee found for '{query}'."

    return "\n".join(
        f"ID: {employee[0]}, "
        f"Name: {employee[1]}, "
        f"Role: {employee[2]}, "
        f"Salary: {employee[3]}, "
        f"Company: {employee[4]}"
        for employee in employees
    )
    
    
    
# ============================================
# Highest Paid Employee At Company
# ============================================

def highest_paid_employee_at_company(company):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name, role, salary, company
        FROM employees
        WHERE company ILIKE %s
        ORDER BY salary DESC
        LIMIT 1
    """, (company,))

    employee = cursor.fetchone()

    cursor.close()
    connection.close()

    if not employee:
        return f"No employees found at {company}."

    return (
        f"Name: {employee[0]}, "
        f"Role: {employee[1]}, "
        f"Salary: {employee[2]}, "
        f"Company: {employee[3]}"
    )
# ============================================
# Compare Company Salaries
# ============================================

def compare_company_salaries(company1, company2):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            company,
            COUNT(*) AS employee_count,
            AVG(salary) AS average_salary,
            MAX(salary) AS highest_salary,
            MIN(salary) AS lowest_salary
        FROM employees
        WHERE company ILIKE %s
           OR company ILIKE %s
        GROUP BY company
        ORDER BY company
    """, (
        company1,
        company2
    ))

    companies = cursor.fetchall()

    cursor.close()
    connection.close()

    if not companies:
        return "No employees found for the specified companies."

    return "\n".join(
        f"Company: {company[0]}, "
        f"Employees: {company[1]}, "
        f"Average Salary: {float(company[2]):.2f}, "
        f"Highest Salary: {company[3]}, "
        f"Lowest Salary: {company[4]}"
        for company in companies
    )
# ============================================
# Pagination
# ============================================

def list_employees_paginated(page=1, page_size=2):

    connection = get_connection()
    cursor = connection.cursor()

    # Total employees
    cursor.execute("""
        SELECT COUNT(*)
        FROM employees
    """)

    total = cursor.fetchone()[0]

    # Calculate offset
    offset = (page - 1) * page_size

    # Get employees for this page
    cursor.execute("""
        SELECT id, name, role, salary
        FROM employees
        ORDER BY id
        LIMIT %s OFFSET %s
    """, (
        page_size,
        offset
    ))

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 1
    )

    if not employees:
        return (
            f"Page {page} of {total_pages}\n"
            f"Total employees: {total}\n\n"
            "No employees found on this page."
        )

    result = (
        f"Page {page} of {total_pages}\n"
        f"Total employees: {total}\n\n"
    )

    result += "\n".join(
        f"ID: {employee[0]}, "
        f"Name: {employee[1]}, "
        f"Role: {employee[2]}, "
        f"Salary: {employee[3]}"
        for employee in employees
    )

    return result


# ============================================
# Advanced Employee Filter
# ============================================

def filter_company_employees(
    role=None,
    min_salary=None,
    max_salary=None,
    page=1,
    page_size=10
):

    connection = get_connection()
    cursor = connection.cursor()

    conditions = []
    values = []

    # Role filter
    if role:
        conditions.append("role ILIKE %s")
        values.append(f"%{role}%")

    # Minimum salary
    if min_salary is not None:
        conditions.append("salary >= %s")
        values.append(min_salary)

    # Maximum salary
    if max_salary is not None:
        conditions.append("salary <= %s")
        values.append(max_salary)

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

    cursor.execute(
        count_query,
        values
    )

    total = cursor.fetchone()[0]







    # Pagination
    offset = (page - 1) * page_size

    query = f"""
        SELECT id, name, role, salary
        FROM employees
        {where_clause}
        ORDER BY salary DESC
        LIMIT %s OFFSET %s
    """

    cursor.execute(
        query,
        values + [page_size, offset]
    )

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 1
    )

    if not employees:
        return (
            f"Page {page} of {total_pages}\n"
            f"Total matching employees: {total}\n\n"
            "No matching employees found."
        )

    result = (
        f"Page {page} of {total_pages}\n"
        f"Total matching employees: {total}\n\n"
    )

    result += "\n".join(
        f"ID: {employee[0]}, "
        f"Name: {employee[1]}, "
        f"Role: {employee[2]}, "
        f"Salary: {employee[3]}"
        for employee in employees
    )

    return result


    return result


# ============================================
# Company Statistics
# ============================================

def get_company_statistics(company):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            company,
            COUNT(*) AS employee_count,
            AVG(salary) AS average_salary,
            MAX(salary) AS highest_salary,
            MIN(salary) AS lowest_salary
        FROM employees
        WHERE company ILIKE %s
        GROUP BY company
    """, (company,))

    stats = cursor.fetchone()

    if not stats:
        cursor.close()
        connection.close()
        return f"No employees found for company '{company}'."

    cursor.execute("""
        SELECT name, role, salary
        FROM employees
        WHERE company ILIKE %s
        ORDER BY salary DESC
        LIMIT 1
    """, (company,))

    highest = cursor.fetchone()

    cursor.execute("""
        SELECT DISTINCT role
        FROM employees
        WHERE company ILIKE %s
        ORDER BY role
    """, (company,))

    roles = cursor.fetchall()

    cursor.close()
    connection.close()

    role_names = ", ".join(role[0] for role in roles)

    return (
        f"Company: {stats[0]}\n"
        f"Employees: {stats[1]}\n"
        f"Average Salary: {float(stats[2]):.2f}\n"
        f"Highest Salary: {stats[3]}\n"
        f"Lowest Salary: {stats[4]}\n"
        f"Highest Paid Employee: {highest[0]}\n"
        f"Highest Paid Role: {highest[1]}\n"
        f"Roles: {role_names}"
    )