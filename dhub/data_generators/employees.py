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
                self.id_manager.training_program_ids.append(program_id)
                programs.append({
                    "program_id": program_id,
                    "program_name": name,
                    "description": fake.text(max_nb_chars=200),
                    "duration_hours": random.choice([2, 4, 8, 16, 24, 40]),
                    "category": category,
                    "offers_certification": random.random() < 0.30,
                })

        return programs

    def generate_employee_training(self) -> list[dict]:
        """Generate employee training enrollment and completion records.

        On average, each employee completes 2-4 training programs.
        """
        training_records = []

        if not self.id_manager.training_program_ids:
            return training_records

        for employee_id in self.id_manager.employee_ids:
            # Each employee enrolls in 2-4 training programs
            num_trainings = random.randint(2, 4)
            employee_programs = random.sample(
                self.id_manager.training_program_ids,
                k=min(num_trainings, len(self.id_manager.training_program_ids))
            )

            for program_id in employee_programs:
                # Enrollment date: sometime after hire date
                enrollment_date = fake.date_between(start_date="-2y", end_date="today")

                # 80% completed, 15% in_progress, 5% enrolled
                status_choice = random.random()
                if status_choice < 0.80:
                    status = "completed"
                    # Completion date 1-8 weeks after enrollment
                    completion_date = enrollment_date + timedelta(days=random.randint(7, 56))
                    score = random.randint(65, 100)
                elif status_choice < 0.95:
                    status = "in_progress"
                    completion_date = None
                    score = None
                else:
                    status = "enrolled"
                    completion_date = None
                    score = None

                training_records.append({
                    "employee_id": employee_id,
                    "program_id": program_id,
                    "enrollment_date": enrollment_date,
                    "completion_date": completion_date,
                    "status": status,
                    "score": score,
                })

        return training_records

    def generate_performance_reviews(self) -> list[dict]:
        """Generate performance review records.

        Active employees get annual reviews. Each employee has 1-3 reviews.
        """
        reviews = []

        # Filter active employees
        active_employees = [
            emp_id for emp_id in self.id_manager.employee_ids
        ]

        for employee_id in active_employees:
            # 1-3 reviews per employee
            num_reviews = random.randint(1, 3)

            for i in range(num_reviews):
                # Review date: spread over last 3 years, annually
                review_date = fake.date_between(
                    start_date=f"-{(num_reviews - i) * 365}d",
                    end_date=f"-{(num_reviews - i - 1) * 365}d" if i < num_reviews - 1 else "today"
                )

                # Reviewer is typically the manager or a senior employee
                available_reviewers = [
                    emp for emp in self.id_manager.employee_ids
                    if emp != employee_id
                ]
                reviewer_id = random.choice(available_reviewers) if available_reviewers else employee_id

                # Rating: weighted towards 3-4 (satisfactory to good)
                rating = random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.02, 0.08, 0.35, 0.40, 0.15],
                    k=1
                )[0]

                # Goals met: percentage (0-100)
                goals_met = random.randint(60, 100)

                # Comments based on rating
                comments_templates = {
                    5: [
                        "Exceptional performance. Consistently exceeds expectations.",
                        "Outstanding contributions to the team and organization.",
                        "Demonstrates exceptional leadership and initiative.",
                    ],
                    4: [
                        "Strong performance. Meets and often exceeds expectations.",
                        "Reliable team member with consistent results.",
                        "Shows good initiative and problem-solving skills.",
                    ],
                    3: [
                        "Satisfactory performance. Meets expectations.",
                        "Solid contributor to the team.",
                        "Performs assigned duties competently.",
                    ],
                    2: [
                        "Below expectations. Improvement needed in several areas.",
                        "Requires additional support to meet performance standards.",
                        "Some concerns about consistency and quality of work.",
                    ],
                    1: [
                        "Unsatisfactory performance. Significant improvement required.",
                        "Does not meet minimum performance standards.",
                        "Performance improvement plan recommended.",
                    ],
                }

                reviews.append({
                    "employee_id": employee_id,
                    "review_date": review_date,
                    "reviewer_id": reviewer_id,
                    "rating": rating,
                    "goals_met": goals_met,
                    "comments": random.choice(comments_templates[rating]),
                })

        return reviews

    def generate_employee_assignments(self, customer_ids: list[str]) -> list[dict]:
        """Generate employee assignments to customers and branches.

        Args:
            customer_ids: List of customer IDs from accounts_db

        Returns:
            List of assignment records
        """
        assignments = []

        # Get customer service reps, loan officers, and insurance agents
        assignable_employees = [
            emp_id for emp_id, role in zip(
                self.id_manager.employee_ids,
                [self.id_manager.get_employee_role(emp_id) for emp_id in self.id_manager.employee_ids]
            )
            if role in ["Customer Service Representative", "Loan Officer", "Insurance Agent"]
        ]

        if not assignable_employees or not customer_ids:
            return assignments

        # Assign 60% of customers to employees
        num_assignments = int(len(customer_ids) * 0.60)
        assigned_customers = random.sample(customer_ids, k=min(num_assignments, len(customer_ids)))

        for customer_id in assigned_customers:
            employee_id = random.choice(assignable_employees)

            # Start date: sometime in the past
            start_date = fake.date_between(start_date="-2y", end_date="-30d")

            # 85% ongoing, 15% ended
            end_date = None
            if random.random() < 0.15:
                end_date = fake.date_between(start_date=start_date, end_date="today")

            assignments.append({
                "employee_id": employee_id,
                "assignment_type": "customer_portfolio",
                "related_entity_id": customer_id,
                "start_date": start_date,
                "end_date": end_date,
            })

        # Add some branch coverage assignments (10-20 assignments)
        num_branch_assignments = random.randint(10, 20)
        for _ in range(num_branch_assignments):
            employee_id = random.choice(self.id_manager.employee_ids)
            branch_code = random.choice(self.branch_codes)

            start_date = fake.date_between(start_date="-1y", end_date="-30d")

            # 70% ongoing
            end_date = None
            if random.random() < 0.30:
                end_date = fake.date_between(start_date=start_date, end_date="today")

            assignments.append({
                "employee_id": employee_id,
                "assignment_type": "branch_coverage",
                "related_entity_id": branch_code,
                "start_date": start_date,
                "end_date": end_date,
            })

        return assignments

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
