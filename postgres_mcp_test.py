from database import (
    list_employees,
    search_employee,
    employees_earning_more_than,
    highest_paid_employee,
    company_search,
    list_employees_paginated,
    filter_company_employees
)


print("\n=== ALL EMPLOYEES ===")
print(list_employees())


print("\n=== SEARCH PRIYA ===")
print(search_employee("Priya"))


print("\n=== SALARY > 70000 ===")
print(employees_earning_more_than(70000))


print("\n=== HIGHEST PAID ===")
print(highest_paid_employee())


print("\n=== AI SEARCH ===")
print(company_search("AI"))


print("\n=== PAGINATION ===")
print(list_employees_paginated(1, 2))


print("\n=== ADVANCED FILTER ===")
print(
    filter_company_employees(
        role="AI",
        min_salary=70000,
        page=1,
        page_size=10
    )
)