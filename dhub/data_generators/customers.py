"""Customer and account data generation."""

import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

from dhub.data_generators.id_manager import IDManager

fake = Faker()


class CustomerGenerator:
    """Generate customer data for accounts_db and customer_db."""

    SEGMENTS = {
        "retail": 0.60,
        "premium": 0.25,
        "corporate": 0.10,
        "private_banking": 0.05,
    }

    CUSTOMER_STATUS = {
        "active": 0.90,
        "dormant": 0.07,
        "closed": 0.03,
    }

    KYC_STATUS = {
        "verified": 0.85,
        "pending": 0.10,
        "expired": 0.05,
    }

    RISK_RATING = {
        "low": 0.70,
        "medium": 0.25,
        "high": 0.05,
    }

    def __init__(self, id_manager: IDManager, num_customers: int = 1200):
        """Initialize customer generator."""
        self.id_manager = id_manager
        self.num_customers = num_customers

    def generate_customers_master(self) -> list[dict]:
        """Generate customer master records for accounts_db."""
        customers = []

        for i in range(self.num_customers):
            customer_id = f"CUST-{uuid.uuid4().hex[:10].upper()}"

            # Age distribution with bell curve
            age = int(random.gauss(42, 15))  # Mean 42, std dev 15
            age = max(18, min(85, age))  # Clamp to 18-85

            birth_date = fake.date_of_birth(minimum_age=age, maximum_age=age)

            # Created date in last 7 years
            created_at = fake.date_time_between(start_date="-7y", end_date="now")

            # Generate phone that fits VARCHAR(20)
            phone = f"{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

            # Store full customer data for profiles
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.email()
            city = fake.city()
            state = fake.state_abbr()
            zip_code = fake.zipcode()
            address = fake.street_address()

            customer = {
                "customer_id": customer_id,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": birth_date,
                "email": email,
                "phone": phone,
                "created_at": created_at,
                # Extra fields for profiles
                "full_address": f"{address}, {city}, {state} {zip_code}",
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "country": "USA",
                "updated_at": created_at,
            }

            customers.append(customer)
            self.id_manager.add_customer(customer_id)

        return customers

    def generate_customer_profiles(self, customers: list[dict]) -> list[dict]:
        """Generate customer profiles for customer_db."""
        profiles = []

        for customer in customers:
            # Weighted random selections
            segment = self._weighted_choice(self.SEGMENTS)
            status = self._weighted_choice(self.CUSTOMER_STATUS)
            kyc_status = self._weighted_choice(self.KYC_STATUS)
            risk_rating = self._weighted_choice(self.RISK_RATING)

            # 80% have assigned agent
            assigned_agent_id = None
            if random.random() < 0.80 and self.id_manager.employee_ids:
                assigned_agent_id = random.choice(self.id_manager.employee_ids)

            profile = {
                "customer_id": customer["customer_id"],
                "full_name": f"{customer['first_name']} {customer['last_name']}",
                "email": customer["email"],
                "phone": customer["phone"],
                "address": customer["full_address"],
                "city": customer["city"],
                "country": customer["country"],
                "customer_segment": segment,
                "customer_status": status,
                "onboarding_date": customer["created_at"].date(),
                "assigned_agent_id": assigned_agent_id,
                "kyc_status": kyc_status,
                "risk_rating": risk_rating,
                "created_at": customer["created_at"],
                "updated_at": customer["updated_at"],
            }

            profiles.append(profile)

        return profiles

    @staticmethod
    def _weighted_choice(choices: dict[str, float]) -> str:
        """Make weighted random choice."""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights, k=1)[0]


class AccountGenerator:
    """Generate account and transaction data."""

    ACCOUNT_TYPES = {
        "checking": 0.50,
        "savings": 0.30,
        "money_market": 0.15,
        "cd": 0.05,
    }

    ACCOUNT_STATUS = {
        "active": 0.92,
        "frozen": 0.05,
        "closed": 0.03,
    }

    BALANCE_RANGES = {
        "checking": (50, 25000),
        "savings": (100, 100000),
        "money_market": (10000, 500000),
        "cd": (5000, 200000),
    }

    def __init__(self, id_manager: IDManager):
        """Initialize account generator."""
        self.id_manager = id_manager

    def generate_accounts(self, customers: list[dict]) -> list[dict]:
        """Generate account records for accounts_db."""
        accounts = []

        # 75% of customers have accounts
        customers_with_accounts = random.sample(
            customers, k=int(len(customers) * 0.75)
        )

        for customer in customers_with_accounts:
            # 25% have multiple accounts
            num_accounts = 2 if random.random() < 0.25 else 1

            for _ in range(num_accounts):
                account_id = f"ACC-{uuid.uuid4().hex[:12].upper()}"
                account_number = f"{random.randint(1000000000, 9999999999)}"

                account_type = CustomerGenerator._weighted_choice(self.ACCOUNT_TYPES)
                status = CustomerGenerator._weighted_choice(self.ACCOUNT_STATUS)

                # Balance based on account type
                balance_range = self.BALANCE_RANGES[account_type]
                balance = round(random.uniform(*balance_range), 2)

                # Opened date after customer created, with some variation
                customer_created = customer["created_at"]
                max_days = (datetime.now() - customer_created).days
                if max_days > 0:
                    days_after = random.randint(0, min(max_days, 365))
                    opened_date = customer_created + timedelta(days=days_after)
                else:
                    opened_date = customer_created

                # Currency
                currency = "USD" if random.random() < 0.95 else random.choice(["EUR", "GBP", "CAD"])

                account = {
                    "account_id": account_id,
                    "account_number": account_number,
                    "customer_id": customer["customer_id"],
                    "account_type": account_type,
                    "balance": balance,
                    "currency": currency,
                    "status": status,
                    "opened_date": opened_date.date(),
                    "created_at": opened_date,
                }

                accounts.append(account)
                self.id_manager.add_account(account_id, customer["customer_id"])

        return accounts
