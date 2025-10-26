"""Loan data generation for loans_db."""

import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from faker import Faker

from dhub.data_generators.id_manager import IDManager

fake = Faker()


class LoanGenerator:
    """Generate loan application and loan data."""

    LOAN_TYPES = {
        "mortgage": 0.35,
        "personal": 0.30,
        "auto": 0.20,
        "business": 0.10,
        "education": 0.05,
    }

    APPLICATION_STATUS = {
        "approved": 0.65,
        "pending": 0.10,
        "rejected": 0.20,
        "withdrawn": 0.05,
    }

    LOAN_STATUS = {
        "active": 0.75,
        "paid_off": 0.20,
        "defaulted": 0.03,
        "restructured": 0.02,
    }

    # Loan parameters by type
    LOAN_PARAMS = {
        "mortgage": {
            "amount_range": (100000, 800000),
            "interest_range": (0.0325, 0.0675),
            "term_months": [180, 240, 300, 360],  # 15, 20, 25, 30 years
        },
        "personal": {
            "amount_range": (5000, 75000),
            "interest_range": (0.0599, 0.1799),
            "term_months": [12, 24, 36, 48, 60],
        },
        "auto": {
            "amount_range": (15000, 80000),
            "interest_range": (0.0399, 0.0899),
            "term_months": [36, 48, 60, 72],
        },
        "business": {
            "amount_range": (25000, 500000),
            "interest_range": (0.0499, 0.1299),
            "term_months": [36, 60, 84, 120],
        },
        "education": {
            "amount_range": (5000, 100000),
            "interest_range": (0.0425, 0.0875),
            "term_months": [60, 84, 120, 180],
        },
    }

    REJECTION_REASONS = [
        "Insufficient credit history",
        "Low credit score",
        "High debt-to-income ratio",
        "Incomplete documentation",
        "Unstable employment history",
        "Insufficient collateral value",
    ]

    COLLATERAL_TYPES = {
        "mortgage": ["property", "real_estate"],
        "auto": ["vehicle"],
        "business": ["equipment", "property", "inventory"],
        "personal": [],  # Usually unsecured
        "education": [],  # Usually unsecured
    }

    CREDIT_GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C"]

    def __init__(self, id_manager: IDManager, scale_factor: float = 1.0):
        """Initialize loan generator.

        Args:
            id_manager: ID manager for cross-database relationships
            scale_factor: Multiplier for dataset size
        """
        self.id_manager = id_manager
        self.scale_factor = scale_factor
        self.base_applications = 400  # Base number of applications at scale 1.0
        self.num_applications = int(self.base_applications * scale_factor)

    def generate_loan_applications(self, customers: list[dict]) -> list[dict]:
        """Generate loan applications.

        ~35% of customers apply for loans.
        """
        applications = []

        if not customers or not self.id_manager.loan_officers:
            return applications

        # Select 35% of customers to apply for loans
        num_applicants = int(len(customers) * 0.35)
        applicants = random.sample(customers, k=min(num_applicants, len(customers)))

        for customer in applicants:
            # Some customers apply multiple times (20% apply twice)
            num_applications = 2 if random.random() < 0.20 else 1

            for _ in range(num_applications):
                application_id = f"LAPP-{uuid.uuid4().hex[:12].upper()}"

                # Loan type
                loan_type = self._weighted_choice(self.LOAN_TYPES)
                params = self.LOAN_PARAMS[loan_type]

                # Requested amount
                requested_amount = round(
                    random.uniform(*params["amount_range"]), 2
                )

                # Application date
                application_date = fake.date_between(
                    start_date="-2y", end_date="today"
                )

                # Status
                status = self._weighted_choice(self.APPLICATION_STATUS)

                # Loan officer
                officer_id = random.choice(self.id_manager.loan_officers)

                # Decision date and approved amount
                decision_date = None
                approved_amount = None
                rejection_reason = None

                if status in ["approved", "rejected"]:
                    # Decision made 1-30 days after application
                    decision_date = application_date + timedelta(
                        days=random.randint(1, 30)
                    )

                    if status == "approved":
                        # Approved amount: 80-100% of requested
                        approved_amount = round(
                            requested_amount * random.uniform(0.80, 1.00), 2
                        )
                        self.id_manager.approved_application_ids.append(application_id)
                    else:
                        rejection_reason = random.choice(self.REJECTION_REASONS)

                application = {
                    "application_id": application_id,
                    "customer_id": customer["customer_id"],
                    "loan_type": loan_type,
                    "requested_amount": requested_amount,
                    "application_date": application_date,
                    "status": status,
                    "officer_id": officer_id,
                    "decision_date": decision_date,
                    "approved_amount": approved_amount,
                    "rejection_reason": rejection_reason,
                }

                applications.append(application)
                self.id_manager.loan_application_ids.append(application_id)

        return applications

    def generate_loans(self, accounts: list[dict]) -> list[dict]:
        """Generate loan records from approved applications.

        Args:
            accounts: List of account records for linking

        Returns:
            List of loan records
        """
        loans = []

        if not self.id_manager.approved_application_ids:
            return loans

        # Create active account mapping for quick lookup
        active_accounts_by_customer = {}
        for account in accounts:
            if account.get("status") == "active":
                customer_id = account["customer_id"]
                if customer_id not in active_accounts_by_customer:
                    active_accounts_by_customer[customer_id] = []
                active_accounts_by_customer[customer_id].append(account["account_id"])

        # Generate loans from approved applications (need to fetch customer_id and loan_type)
        # We'll use the approved_application_ids
        for application_id in self.id_manager.approved_application_ids:
            loan_id = f"LOAN-{uuid.uuid4().hex[:12].upper()}"
            loan_number = f"{random.randint(1000000000, 9999999999)}"

            # We need to link back to customer - this is a simplified approach
            # In real implementation, we'd store application details in id_manager
            # For now, randomly select from customers who have applications
            if not self.id_manager.customer_ids:
                continue

            customer_id = random.choice(self.id_manager.customer_ids)

            # Randomly select loan type for this generation
            loan_type = random.choice(list(self.LOAN_PARAMS.keys()))
            params = self.LOAN_PARAMS[loan_type]

            # Linked account (if customer has one)
            linked_account_id = None
            if customer_id in active_accounts_by_customer:
                linked_account_id = random.choice(
                    active_accounts_by_customer[customer_id]
                )

            # Principal amount
            principal_amount = round(
                random.uniform(*params["amount_range"]), 2
            )

            # Interest rate
            interest_rate = round(
                random.uniform(*params["interest_range"]), 4
            )

            # Term
            term_months = random.choice(params["term_months"])

            # Disbursement date (after application)
            disbursement_date = fake.date_between(
                start_date="-2y", end_date="-30d"
            )

            # Maturity date
            maturity_date = disbursement_date + timedelta(
                days=term_months * 30
            )

            # Loan status
            loan_status = self._weighted_choice(self.LOAN_STATUS)

            # Outstanding balance
            if loan_status == "paid_off":
                outstanding_balance = 0.0
            elif loan_status == "defaulted":
                # 40-90% still outstanding
                outstanding_balance = round(
                    principal_amount * random.uniform(0.40, 0.90), 2
                )
            else:  # active or restructured
                # Calculate based on how much time has passed
                months_elapsed = (
                    (datetime.now().date() - disbursement_date).days // 30
                )
                progress = min(months_elapsed / term_months, 1.0)
                outstanding_balance = round(
                    principal_amount * (1 - progress * random.uniform(0.7, 0.95)), 2
                )

            # Default status
            default_status = loan_status == "defaulted"

            # Approved by
            approved_by = (
                random.choice(self.id_manager.loan_officers)
                if self.id_manager.loan_officers
                else None
            )

            loan = {
                "loan_id": loan_id,
                "application_id": application_id,
                "loan_number": loan_number,
                "customer_id": customer_id,
                "linked_account_id": linked_account_id,
                "loan_type": loan_type,
                "principal_amount": principal_amount,
                "interest_rate": interest_rate,
                "term_months": term_months,
                "disbursement_date": disbursement_date,
                "maturity_date": maturity_date,
                "loan_status": loan_status,
                "outstanding_balance": outstanding_balance,
                "default_status": default_status,
                "approved_by": approved_by,
            }

            loans.append(loan)
            self.id_manager.loan_ids.append(loan_id)

        return loans

    def generate_collateral(self, loans: list[dict]) -> list[dict]:
        """Generate collateral for secured loans.

        Args:
            loans: List of loan records

        Returns:
            List of collateral records
        """
        collateral_records = []

        for loan in loans:
            loan_type = loan["loan_type"]

            # Only certain loan types have collateral
            if loan_type not in self.COLLATERAL_TYPES:
                continue

            collateral_types = self.COLLATERAL_TYPES[loan_type]
            if not collateral_types:
                continue

            # 80% of eligible loans have collateral
            if random.random() < 0.80:
                collateral_id = f"COL-{uuid.uuid4().hex[:12].upper()}"
                collateral_type = random.choice(collateral_types)

                # Appraised value: 110-150% of loan principal
                appraised_value = round(
                    loan["principal_amount"] * random.uniform(1.10, 1.50), 2
                )

                # Appraisal date: around disbursement date
                appraisal_date = loan["disbursement_date"] - timedelta(
                    days=random.randint(7, 30)
                )

                # LTV ratio
                ltv_ratio = round(
                    loan["principal_amount"] / appraised_value, 4
                )

                # Description
                descriptions = {
                    "property": f"{fake.street_address()}, {fake.city()}",
                    "real_estate": f"Commercial property at {fake.street_address()}",
                    "vehicle": f"{random.randint(2015, 2024)} {fake.company()} {random.choice(['Sedan', 'SUV', 'Truck'])}",
                    "equipment": f"Business equipment: {fake.bs()}",
                    "inventory": "Business inventory and stock",
                }

                collateral_records.append({
                    "collateral_id": collateral_id,
                    "loan_id": loan["loan_id"],
                    "collateral_type": collateral_type,
                    "description": descriptions.get(collateral_type, "Collateral asset"),
                    "appraised_value": appraised_value,
                    "appraisal_date": appraisal_date,
                    "ltv_ratio": ltv_ratio,
                })

        return collateral_records

    def generate_repayment_schedule(self, loans: list[dict]) -> list[dict]:
        """Generate repayment schedules for loans.

        Creates monthly installments for each loan.

        Args:
            loans: List of loan records

        Returns:
            List of repayment schedule records
        """
        schedules = []

        for loan in loans:
            principal = loan["principal_amount"]
            rate = loan["interest_rate"]
            term = loan["term_months"]
            disbursement = loan["disbursement_date"]

            # Calculate monthly payment using amortization formula
            monthly_rate = rate / 12
            monthly_payment = (
                principal * (monthly_rate * (1 + monthly_rate) ** term)
                / ((1 + monthly_rate) ** term - 1)
            )

            remaining_balance = principal

            for i in range(1, term + 1):
                # Due date
                due_date = disbursement + timedelta(days=i * 30)

                # Interest portion
                interest_amount = round(remaining_balance * monthly_rate, 2)

                # Principal portion
                principal_amount = round(monthly_payment - interest_amount, 2)

                # Adjust last payment for rounding
                if i == term:
                    principal_amount = round(remaining_balance, 2)

                total_amount = round(principal_amount + interest_amount, 2)

                # Update remaining balance
                remaining_balance -= principal_amount

                # Payment status and date
                payment_status = "pending"
                payment_date = None

                # If due date is in the past
                if due_date < datetime.now().date():
                    # Determine if paid
                    if loan["loan_status"] == "paid_off":
                        payment_status = "paid"
                        payment_date = due_date + timedelta(
                            days=random.randint(-5, 5)
                        )
                    elif loan["loan_status"] == "defaulted":
                        # 50% of past payments are missed
                        if random.random() < 0.50:
                            payment_status = "missed"
                        else:
                            payment_status = "late"
                            payment_date = due_date + timedelta(
                                days=random.randint(5, 30)
                            )
                    else:  # active or restructured
                        # 95% paid on time
                        if random.random() < 0.95:
                            payment_status = "paid"
                            payment_date = due_date + timedelta(
                                days=random.randint(-3, 3)
                            )
                        else:
                            payment_status = "late"
                            payment_date = due_date + timedelta(
                                days=random.randint(5, 15)
                            )

                schedules.append({
                    "loan_id": loan["loan_id"],
                    "installment_number": i,
                    "due_date": due_date,
                    "principal_amount": principal_amount,
                    "interest_amount": interest_amount,
                    "total_amount": total_amount,
                    "payment_date": payment_date,
                    "payment_status": payment_status,
                })

        return schedules

    def generate_loan_guarantors(self, loans: list[dict]) -> list[dict]:
        """Generate guarantor records for loans.

        ~25% of loans have guarantors.

        Args:
            loans: List of loan records

        Returns:
            List of guarantor records
        """
        guarantors = []

        # 25% of loans have guarantors
        loans_with_guarantors = random.sample(
            loans, k=int(len(loans) * 0.25)
        )

        relationships = [
            "spouse", "parent", "sibling", "business_partner",
            "family_member", "friend", "co-signer"
        ]

        for loan in loans_with_guarantors:
            # 70% have 1 guarantor, 30% have 2
            num_guarantors = 2 if random.random() < 0.30 else 1

            for _ in range(num_guarantors):
                guarantor_name = fake.name()
                relationship = random.choice(relationships)

                # Contact info
                contact_info = f"{fake.email()}, {fake.phone_number()}"

                # Guarantee amount: 50-100% of loan principal
                guarantee_amount = round(
                    loan["principal_amount"] * random.uniform(0.50, 1.00), 2
                )

                guarantors.append({
                    "loan_id": loan["loan_id"],
                    "guarantor_name": guarantor_name,
                    "relationship": relationship,
                    "contact_info": contact_info,
                    "guarantee_amount": guarantee_amount,
                })

        return guarantors

    def generate_risk_assessments(
        self, applications: list[dict], loans: list[dict]
    ) -> list[dict]:
        """Generate risk assessments for applications and loans.

        Args:
            applications: List of loan applications
            loans: List of loans

        Returns:
            List of risk assessment records
        """
        assessments = []

        # Assess all applications
        for application in applications:
            assessment_date = application["application_date"]

            # Risk score: 300-850 (credit score range)
            risk_score = random.randint(550, 850)

            # PD (Probability of Default): correlated with risk score
            if risk_score >= 750:
                pd_probability = round(random.uniform(0.01, 0.05), 4)
                credit_grade = random.choice(["AAA", "AA", "A"])
            elif risk_score >= 650:
                pd_probability = round(random.uniform(0.05, 0.15), 4)
                credit_grade = random.choice(["BBB", "BB"])
            else:
                pd_probability = round(random.uniform(0.15, 0.35), 4)
                credit_grade = random.choice(["B", "CCC", "CC", "C"])

            # Assessed by
            assessed_by = (
                random.choice(self.id_manager.compliance_officers)
                if self.id_manager.compliance_officers
                else (
                    random.choice(self.id_manager.employee_ids)
                    if self.id_manager.employee_ids
                    else None
                )
            )

            assessments.append({
                "loan_id": None,
                "application_id": application["application_id"],
                "assessment_date": assessment_date,
                "risk_score": risk_score,
                "pd_probability": pd_probability,
                "credit_grade": credit_grade,
                "assessed_by": assessed_by,
            })

        # Assess 40% of active loans (periodic reassessment)
        loans_to_assess = random.sample(
            loans, k=int(len(loans) * 0.40)
        )

        for loan in loans_to_assess:
            # Assessment date: some time after disbursement
            days_after = random.randint(180, 730)  # 6 months to 2 years
            assessment_date = loan["disbursement_date"] + timedelta(days=days_after)

            # Ensure assessment date is not in future
            if assessment_date > datetime.now().date():
                assessment_date = datetime.now().date()

            # Risk score adjusts based on loan status
            if loan["loan_status"] == "defaulted":
                risk_score = random.randint(300, 550)
                pd_probability = round(random.uniform(0.50, 0.95), 4)
                credit_grade = random.choice(["CCC", "CC", "C"])
            elif loan["loan_status"] == "paid_off":
                risk_score = random.randint(700, 850)
                pd_probability = round(random.uniform(0.01, 0.05), 4)
                credit_grade = random.choice(["AAA", "AA", "A"])
            else:
                risk_score = random.randint(600, 800)
                pd_probability = round(random.uniform(0.05, 0.20), 4)
                credit_grade = random.choice(["BBB", "BB", "B"])

            assessed_by = (
                random.choice(self.id_manager.compliance_officers)
                if self.id_manager.compliance_officers
                else (
                    random.choice(self.id_manager.employee_ids)
                    if self.id_manager.employee_ids
                    else None
                )
            )

            assessments.append({
                "loan_id": loan["loan_id"],
                "application_id": None,
                "assessment_date": assessment_date,
                "risk_score": risk_score,
                "pd_probability": pd_probability,
                "credit_grade": credit_grade,
                "assessed_by": assessed_by,
            })

        return assessments

    @staticmethod
    def _weighted_choice(choices: dict[str, float]) -> str:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights, k=1)[0]
