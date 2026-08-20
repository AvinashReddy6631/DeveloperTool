from mcp.server import MCPServer
import httpx


# PostgreSQL database functions
from database import (
    list_employees as db_list_employees,
    search_employee as db_search_employee,
    employees_earning_more_than as db_employees_earning_more_than,
    highest_paid_employee as db_highest_paid_employee,
    highest_paid_employee_at_company as db_highest_paid_employee_at_company,
    compare_company_salaries as db_compare_company_salaries,
    get_company_statistics as db_get_company_statistics,
    company_search as db_company_search,
    list_employees_paginated as db_list_employees_paginated,
    filter_company_employees as db_filter_company_employees,
)


# ============================================
# MCP SERVER
# ============================================

mcp = MCPServer("My First MCP Server")


# ============================================
# BASIC CALCULATOR TOOLS
# ============================================

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


# ============================================
# DEVELOPER RESOURCE
# ============================================

@mcp.resource("info://developer")
def developer_info() -> str:
    """Information about an AI developer."""

    return """
AI Developer Skills:
Python
Machine Learning
Generative AI
RAG
AI Agents
MCP
FastAPI
Docker
"""


# ============================================
# DEVELOPER INFORMATION TOOL
# ============================================

@mcp.tool()
def get_developer_info() -> str:
    """Get information about the AI developer and their technical skills."""

    return developer_info()


# ============================================
# INTERVIEW PROMPT
# ============================================

@mcp.prompt()
def interview_prompt(role: str) -> str:
    """Generate an interview preparation prompt."""

    return f"""
Prepare me for a {role} interview.

Give me:

1. Technical questions
2. Coding questions
3. System design questions
4. Behavioral questions
5. Model answers
"""


# ============================================
# WEATHER TOOL
# ============================================

@mcp.tool()
async def get_weather(city: str) -> str:
    """Get the current weather for a city."""

    url = "https://wttr.in"

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{url}/{city}?format=3"
        )

    return response.text


# ============================================
# POSTGRESQL — LIST EMPLOYEES
# ============================================

@mcp.tool()
def list_employees() -> str:
    """
    List all employees from the PostgreSQL company database.
    """

    return db_list_employees()


# ============================================
# POSTGRESQL — SEARCH EMPLOYEE
# ============================================

@mcp.tool()
def search_employee(name: str) -> str:
    """
    Search for an employee by name.
    """

    return db_search_employee(name)


# ============================================
# POSTGRESQL — SALARY FILTER
# ============================================

@mcp.tool()
def employees_earning_more_than(min_salary: int) -> str:
    """
    Find employees earning more than the specified salary.
    """

    return db_employees_earning_more_than(min_salary)


# ============================================
# POSTGRESQL — HIGHEST PAID
# ============================================

@mcp.tool()
def highest_paid_employee() -> str:
    """
    Find the employee with the highest salary.
    """

    return db_highest_paid_employee()


# ============================================
# POSTGRESQL — COMPANY SEARCH
# ============================================
@mcp.tool()
def company_search(query: str) -> str:
    """
    Search company information and employee-company relationships.

    Use this tool when the user asks:
    - Which companies are in the database?
    - What companies exist?
    - Which company does an employee work for?
    - Find employees at a specific company.
    - Search for a company by name.
    - Find company information related to an employee.

    The query can be a company name, employee name, role,
    or a general company-related search.
    """

    return db_company_search(query)

# ============================================
# POSTGRESQL — PAGINATION
# ============================================

@mcp.tool()
def list_employees_paginated(
    page: int = 1,
    page_size: int = 2
) -> str:
    """
    Get employees using pagination.

    Useful when a company has a large number
    of employees and all records should not
    be returned at once.
    """

    if page < 1:
        return "Page must be greater than or equal to 1."

    if page_size < 1 or page_size > 100:
        return "Page size must be between 1 and 100."

    return db_list_employees_paginated(
        page=page,
        page_size=page_size
    )


# ============================================
# POSTGRESQL — ADVANCED FILTER
# ============================================

@mcp.tool()
def filter_company_employees(
    role: str = "",
    min_salary: int = 0,
    max_salary: int = 0,
    page: int = 1,
    page_size: int = 10
) -> str:
    """
    Filter company employees by role and salary.

    Supports pagination.

    Examples:

    Find AI employees
    Find employees earning above 70000
    Find ML employees earning between 70000 and 90000
    """

    # Validate page
    if page < 1:
        return "Page must be greater than or equal to 1."

    # Validate page size
    if page_size < 1 or page_size > 100:
        return "Page size must be between 1 and 100."

    # Validate salaries
    if min_salary < 0:
        return "Minimum salary cannot be negative."

    if max_salary < 0:
        return "Maximum salary cannot be negative."

    if min_salary and max_salary:

        if min_salary > max_salary:
            return "Minimum salary cannot be greater than maximum salary."

    return db_filter_company_employees(
        role=role or None,
        min_salary=min_salary if min_salary > 0 else None,
        max_salary=max_salary if max_salary > 0 else None,
        page=page,
        page_size=page_size
    )



# ============================================
# POSTGRESQL — COMPANY STATISTICS
# ============================================

@mcp.tool()
def get_company_statistics(company: str) -> str:
    """
    Get detailed statistical analysis for ONE specific company.

    ALWAYS prefer this tool when the user asks for:
    - Complete analysis of a company
    - Full analysis of Google, Microsoft, Amazon, etc.
    - Company salary statistics
    - Average salary at a company
    - Highest and lowest salary at a company
    - Highest-paid employee at a company
    - Roles at a company

    Do NOT use list_employees for a company-specific analysis.

    This tool returns:
    - Employee count
    - Average salary
    - Highest salary
    - Lowest salary
    - Highest-paid employee
    - Highest-paid role
    - Roles represented
    """
    return db_get_company_statistics(company)
# ============================================
# START MCP SERVER
# ============================================

if __name__ == "__main__":
    mcp.run()