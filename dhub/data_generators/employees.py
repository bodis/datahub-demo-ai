"""Employee data generation for employees_db."""

import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

from dhub.data_generators.id_manager import IDManager
from dhub.data_generators.unique_generator import UniqueValueGenerator

fake = Faker()


class EmployeeGenerator:
    """Generate employee and department data."""

    DEPARTMENTS = [
        ("retail_banking", "Retail Banking"),
        ("lending", "Lending"),
        ("insurance", "Insurance"),
        ("compliance", "Compliance & Risk"),
        ("operations", "Operations"),
        ("customer_service", "Customer Service"),
        ("risk", "Risk Management"),
        ("it", "Information Technology"),
        ("hr", "Human Resources"),
        ("finance", "Finance"),
        ("audit", "Internal Audit"),
        ("marketing", "Marketing"),
    ]

    ROLES_DISTRIBUTION = {
        "Customer Service Representative": 0.40,
        "Loan Officer": 0.20,
        "Insurance Agent": 0.15,
        "Compliance Officer": 0.10,
        "Branch Manager": 0.05,
        "Risk Analyst": 0.03,
        "IT Specialist": 0.03,
        "HR Specialist": 0.02,
        "Marketing Specialist": 0.02,
    }

    SALARY_RANGES = {
        "Customer Service Representative": (35000, 55000),
        "Loan Officer": (50000, 80000),
        "Insurance Agent": (45000, 75000),
        "Compliance Officer": (60000, 95000),
        "Branch Manager": (70000, 120000),
        "Risk Analyst": (65000, 100000),
        "IT Specialist": (70000, 110000),
        "HR Specialist": (55000, 85000),
        "Marketing Specialist": (60000, 90000),
    }

    def __init__(self, id_manager: IDManager, num_employees: int = 150):
        """Initialize employee generator."""
        self.id_manager = id_manager
        self.num_employees = num_employees
        self.branch_codes = [f"BR{str(i).zfill(3)}" for i in range(1, 21)]  # 20 branches
        self.unique_gen = UniqueValueGenerator(fake)

    def generate_departments(self) -> list[dict]:
        """Generate department records."""
        departments = []

        for code, name in self.DEPARTMENTS:
            dept_id = f"DEPT-{uuid.uuid4().hex[:8].upper()}"
            self.id_manager.department_ids.append(dept_id)

            departments.append({
                "department_id": dept_id,
                "department_name": name,
                "department_head_id": None,  # Will update after employees
                "budget": round(random.uniform(500000, 5000000), 2),
            })

        return departments

    def generate_employees(self) -> list[dict]:
        """Generate employee records."""
        employees = []
        roles_list = []

        # Build roles list based on distribution
        for role, percentage in self.ROLES_DISTRIBUTION.items():
            count = int(self.num_employees * percentage)
            roles_list.extend([role] * count)

        # Fill remaining slots
        while len(roles_list) < self.num_employees:
            roles_list.append(random.choice(list(self.ROLES_DISTRIBUTION.keys())))

        random.shuffle(roles_list)

        # Generate employees
        for i, role in enumerate(roles_list):
            employee_id = f"EMP-{uuid.uuid4().hex[:8].upper()}"
            employee_number = f"E{str(10000 + i)}"  # E10000, E10001, etc.

            # Determine department based on role
            dept_id = self._get_department_for_role(role)

            # Hire date in last 10 years
            hire_date = fake.date_between(start_date="-10y", end_date="today")

            # 5% terminated
            termination_date = None
            employment_status = "active"
            if random.random() < 0.05:
                termination_date = fake.date_between(start_date=hire_date, end_date="today")
                employment_status = "terminated"

            # Manager (70% have managers, 30% senior/independent)
            manager_id = None
            if random.random() < 0.70 and len(self.id_manager.employee_ids) > 0:
                manager_id = random.choice(self.id_manager.employee_ids)

            # Salary
            salary_range = self.SALARY_RANGES.get(role, (40000, 70000))
            salary = round(random.uniform(*salary_range), 2)

            # Generate unique email and phone
            email = self.unique_gen.generate_unique_email()
            phone = self.unique_gen.generate_unique_phone()

            employee = {
                "employee_id": employee_id,
                "employee_number": employee_number,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": email,
                "phone": phone,
                "role": role,
                "department": self._get_department_name(dept_id),
                "branch_code": random.choice(self.branch_codes),
                "manager_id": manager_id,
                "hire_date": hire_date,
                "termination_date": termination_date,
                "employment_status": employment_status,
                "salary": salary,
            }

            employees.append(employee)
            self.id_manager.add_employee(employee_id, role)

        return employees

    def generate_training_programs(self) -> list[dict]:
        """Generate training program records."""
        programs = []
        program_types = {
            "compliance": ["AML Training", "KYC Procedures", "Regulatory Updates", "Ethics Training"],
            "product": ["Loan Products Overview", "Insurance Fundamentals", "Investment Products"],
            "customer_service": ["Customer Communication", "Conflict Resolution", "Sales Techniques"],
            "technical": ["Core Banking System", "CRM Software", "Data Analytics"],
            "leadership": ["Team Management", "Performance Reviews", "Strategic Planning"],
        }

        for category, names in program_types.items():
            for name in names:
                program_id = f"PROG-{uuid.uuid4().hex[:6].upper()}"
                programs.append({
                    "program_id": program_id,
                    "program_name": name,
                    "description": fake.text(max_nb_chars=200),
                    "duration_hours": random.choice([2, 4, 8, 16, 24, 40]),
                    "category": category,
                    "offers_certification": random.random() < 0.30,
                })

        return programs

    def _get_department_for_role(self, role: str) -> str:
        """Get department ID based on role."""
        if not self.id_manager.department_ids:
            return self.id_manager.department_ids[0] if self.id_manager.department_ids else ""

        role_lower = role.lower()
        if "customer service" in role_lower:
            return self.id_manager.department_ids[5]  # customer_service
        elif "loan" in role_lower:
            return self.id_manager.department_ids[1]  # lending
        elif "insurance" in role_lower:
            return self.id_manager.department_ids[2]  # insurance
        elif "compliance" in role_lower:
            return self.id_manager.department_ids[3]  # compliance
        elif "risk" in role_lower:
            return self.id_manager.department_ids[6]  # risk
        elif "it" in role_lower or "specialist" in role_lower and "IT" in role:
            return self.id_manager.department_ids[7]  # it
        elif "hr" in role_lower:
            return self.id_manager.department_ids[8]  # hr
        elif "marketing" in role_lower:
            return self.id_manager.department_ids[11]  # marketing
        elif "manager" in role_lower:
            return self.id_manager.department_ids[0]  # retail_banking
        else:
            return random.choice(self.id_manager.department_ids)

    def _get_department_name(self, dept_id: str) -> str:
        """Get department name from ID."""
        if not dept_id or not self.id_manager.department_ids:
            return "Unknown"

        try:
            idx = self.id_manager.department_ids.index(dept_id)
            return self.DEPARTMENTS[idx][1]
        except (ValueError, IndexError):
            return "Unknown"
