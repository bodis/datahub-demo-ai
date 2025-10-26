"""Customer and account data generation."""

import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

from dhub.data_generators.id_manager import IDManager
from dhub.data_generators.unique_generator import UniqueValueGenerator

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
        self.unique_gen = UniqueValueGenerator(fake)

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

            # Generate unique email and phone
            email = self.unique_gen.generate_unique_email()
            phone = self.unique_gen.generate_unique_phone()

            # Store full customer data for profiles
            first_name = fake.first_name()
            last_name = fake.last_name()
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

    def generate_account_relationships(self, accounts: list[dict]) -> list[dict]:
        """Generate account relationships.

        Creates relationships for:
        - 20% of accounts: 1 connected account
        - 5% of accounts: 2 connected accounts
        """
        relationships = []

        # Only use active accounts for relationships
        active_accounts = [acc for acc in accounts if acc["status"] == "active"]

        if len(active_accounts) < 2:
            return relationships

        # Determine which accounts will have relationships
        # 5% get 2 connections, 20% get 1 connection (25% total)
        accounts_needing_relationships = []

        # First, select 5% for 2 connections
        two_connection_count = int(len(active_accounts) * 0.05)
        accounts_with_two = random.sample(active_accounts, k=min(two_connection_count, len(active_accounts)))

        # Then, select 20% for 1 connection (excluding those with 2)
        remaining_accounts = [acc for acc in active_accounts if acc not in accounts_with_two]
        one_connection_count = int(len(active_accounts) * 0.20)
        accounts_with_one = random.sample(remaining_accounts, k=min(one_connection_count, len(remaining_accounts)))

        relationship_types = ["joint_owner", "beneficiary", "authorized_user", "linked_savings"]

        # Create relationships for accounts with 2 connections
        for account in accounts_with_two:
            # Select 2 different related accounts (excluding itself)
            available = [acc for acc in active_accounts if acc["account_id"] != account["account_id"]]
            if len(available) >= 2:
                related_accounts = random.sample(available, k=2)

                for related in related_accounts:
                    relationship = {
                        "primary_account_id": account["account_id"],
                        "related_account_id": related["account_id"],
                        "relationship_type": random.choice(relationship_types),
                        "created_at": max(account["created_at"], related["created_at"]),
                    }
                    relationships.append(relationship)

        # Create relationships for accounts with 1 connection
        for account in accounts_with_one:
            # Select 1 related account (excluding itself)
            available = [acc for acc in active_accounts if acc["account_id"] != account["account_id"]]
            if available:
                related = random.choice(available)

                relationship = {
                    "primary_account_id": account["account_id"],
                    "related_account_id": related["account_id"],
                    "relationship_type": random.choice(relationship_types),
                    "created_at": max(account["created_at"], related["created_at"]),
                }
                relationships.append(relationship)

        return relationships

    def generate_transactions(self, accounts: list[dict]) -> list[dict]:
        """Generate transactions for accounts.

        Creates 10-20x more transactions than accounts.
        Distribution:
        - 70% spending (withdrawal, payment, fee)
        - 30% income (deposit, salary, interest)
        """
        transactions = []

        # Calculate total transactions (10-20x accounts)
        transaction_multiplier = random.uniform(10, 20)
        total_transactions = int(len(accounts) * transaction_multiplier)

        # Transaction types with weights
        spending_types = {
            "withdrawal": 0.40,
            "payment": 0.45,
            "fee": 0.15,
        }

        income_types = {
            "deposit": 0.50,
            "salary": 0.30,
            "interest": 0.15,
            "refund": 0.05,
        }

        # Generate transactions
        for i in range(total_transactions):
            # Select random account
            account = random.choice(accounts)

            # Determine if spending or income (70% spending, 30% income)
            is_spending = random.random() < 0.70

            if is_spending:
                transaction_type = CustomerGenerator._weighted_choice(spending_types)
                # Spending amount based on account type and balance
                max_amount = min(account["balance"] * 0.3, 5000)  # Max 30% of balance or $5000
                amount = -round(random.uniform(5, max_amount), 2) if max_amount > 5 else -round(random.uniform(1, 50), 2)
            else:
                transaction_type = CustomerGenerator._weighted_choice(income_types)
                # Income amount
                if transaction_type == "salary":
                    amount = round(random.uniform(1000, 8000), 2)
                elif transaction_type == "deposit":
                    amount = round(random.uniform(50, 3000), 2)
                elif transaction_type == "interest":
                    amount = round(account["balance"] * random.uniform(0.001, 0.01), 2)
                else:  # refund
                    amount = round(random.uniform(10, 500), 2)

            # Transaction date: between account opening and now
            opened_date = account["opened_date"] if isinstance(account["opened_date"], datetime) else datetime.combine(account["opened_date"], datetime.min.time())
            days_since_opened = (datetime.now() - opened_date).days

            if days_since_opened > 0:
                random_days = random.randint(0, days_since_opened)
                transaction_date = opened_date + timedelta(days=random_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            else:
                transaction_date = opened_date

            # Calculate balance after (simplified - actual balance would need sorted transactions)
            balance_after = account["balance"] + amount

            # Generate transaction ID
            transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"

            # Description based on type
            descriptions = {
                "withdrawal": ["ATM Withdrawal", "Cash Withdrawal", "Branch Withdrawal"],
                "payment": [f"Payment to {fake.company()}", f"Online Purchase - {fake.company()}", f"Bill Payment - {fake.bs()}"],
                "fee": ["Monthly Maintenance Fee", "ATM Fee", "Overdraft Fee", "Wire Transfer Fee"],
                "deposit": ["Cash Deposit", "Check Deposit", "Mobile Deposit"],
                "salary": [f"Salary - {fake.company()}", "Payroll Deposit", "Direct Deposit"],
                "interest": ["Interest Credit", "Savings Interest"],
                "refund": [f"Refund from {fake.company()}", "Purchase Refund", "Credit Adjustment"],
            }

            description = random.choice(descriptions.get(transaction_type, ["Transaction"]))

            # Counterparty account (for transfers and payments)
            counterparty = None
            if transaction_type in ["payment", "withdrawal"] and random.random() < 0.3:
                counterparty = f"{random.randint(1000000000, 9999999999)}"

            # Processed by employee (30% are manual, 70% automated)
            processed_by = None
            if random.random() < 0.30 and self.id_manager.employee_ids:
                processed_by = random.choice(self.id_manager.employee_ids)

            transaction = {
                "transaction_id": transaction_id,
                "account_id": account["account_id"],
                "transaction_type": transaction_type,
                "transaction_amount": amount,
                "transaction_date": transaction_date,
                "description": description,
                "balance_after": balance_after,
                "counterparty_account": counterparty,
                "processed_by": processed_by,
            }

            transactions.append(transaction)

        # Sort by transaction date for more realistic data
        transactions.sort(key=lambda x: x["transaction_date"])

        return transactions


class CRMGenerator:
    """Generate CRM data for customer_db (interactions, complaints, campaigns)."""

    INTERACTION_TYPES = {
        "inquiry": 0.35,
        "support": 0.30,
        "complaint": 0.15,
        "account_update": 0.10,
        "product_inquiry": 0.10,
    }

    CHANNELS = {
        "phone": 0.30,
        "email": 0.25,
        "web": 0.20,
        "mobile_app": 0.15,
        "branch": 0.10,
    }

    OUTCOMES = {
        "resolved": 0.70,
        "follow_up_needed": 0.20,
        "escalated": 0.10,
    }

    COMPLAINT_TYPES = {
        "service": 0.35,
        "fee": 0.25,
        "product": 0.20,
        "fraud": 0.10,
        "other": 0.10,
    }

    COMPLAINT_STATUS = {
        "resolved": 0.60,
        "investigating": 0.20,
        "closed": 0.15,
        "open": 0.05,
    }

    PRIORITY = {
        "low": 0.50,
        "medium": 0.30,
        "high": 0.15,
        "critical": 0.05,
    }

    CAMPAIGN_TYPES = {
        "email": 0.40,
        "digital": 0.30,
        "cross_sell": 0.20,
        "direct_mail": 0.10,
    }

    RESPONSE_TYPES = {
        "opened": 0.40,
        "clicked": 0.30,
        "purchased": 0.20,
        "unsubscribed": 0.10,
    }

    def __init__(self, id_manager: IDManager, scale_factor: float = 1.0):
        """Initialize CRM generator."""
        self.id_manager = id_manager
        self.scale_factor = scale_factor

    def generate_interactions(self, customers: list[dict]) -> list[dict]:
        """Generate customer interactions (0-5 per customer)."""
        interactions = []

        for customer in customers:
            # Each customer has 0-5 interactions
            num_interactions = random.choices(
                [0, 1, 2, 3, 4, 5],
                weights=[0.20, 0.25, 0.25, 0.15, 0.10, 0.05],
                k=1
            )[0]

            customer_created = customer["created_at"]

            for _ in range(num_interactions):
                interaction_id = f"INT-{uuid.uuid4().hex[:12].upper()}"

                interaction_type = CustomerGenerator._weighted_choice(self.INTERACTION_TYPES)
                channel = CustomerGenerator._weighted_choice(self.CHANNELS)
                outcome = CustomerGenerator._weighted_choice(self.OUTCOMES)

                # Interaction date: between customer creation and now
                days_since = (datetime.now() - customer_created).days
                if days_since > 0:
                    random_days = random.randint(0, days_since)
                    interaction_date = customer_created + timedelta(
                        days=random_days,
                        hours=random.randint(8, 18),
                        minutes=random.randint(0, 59)
                    )
                else:
                    interaction_date = customer_created

                # Duration based on channel and type
                if channel in ["phone", "branch"]:
                    duration = random.randint(5, 45)
                elif channel == "web":
                    duration = random.randint(2, 15)
                else:  # email, mobile_app
                    duration = random.randint(1, 10)

                # Handled by employee (80% of the time)
                handled_by = None
                if random.random() < 0.80 and self.id_manager.employee_ids:
                    handled_by = random.choice(self.id_manager.employee_ids)

                # Notes
                notes_templates = [
                    f"Customer inquired about {fake.bs()}",
                    f"Discussed {interaction_type} regarding account services",
                    f"Provided support for {fake.catch_phrase().lower()}",
                    f"Customer requested information about {fake.bs()}",
                    f"Handled {interaction_type} through {channel} channel",
                ]

                interaction = {
                    "interaction_id": interaction_id,
                    "customer_id": customer["customer_id"],
                    "interaction_type": interaction_type,
                    "channel": channel,
                    "interaction_date": interaction_date,
                    "duration_minutes": duration,
                    "notes": random.choice(notes_templates),
                    "handled_by": handled_by,
                    "outcome": outcome,
                }

                interactions.append(interaction)

        return interactions

    def generate_satisfaction_surveys(self, interactions: list[dict], customers: list[dict]) -> list[dict]:
        """Generate satisfaction surveys (30% of interactions get surveyed)."""
        surveys = []

        # 30% of interactions get a survey
        surveyed_interactions = random.sample(interactions, k=int(len(interactions) * 0.30))

        for interaction in surveyed_interactions:
            # NPS score: 0-10 (weighted towards positive)
            nps_score = random.choices(
                range(11),
                weights=[2, 2, 3, 4, 5, 6, 8, 12, 15, 20, 23],
                k=1
            )[0]

            # Satisfaction rating: 1-5 stars (correlated with NPS)
            if nps_score >= 9:
                satisfaction = random.choices([4, 5], weights=[0.3, 0.7], k=1)[0]
            elif nps_score >= 7:
                satisfaction = random.choices([3, 4, 5], weights=[0.2, 0.5, 0.3], k=1)[0]
            elif nps_score >= 5:
                satisfaction = random.choices([2, 3, 4], weights=[0.3, 0.5, 0.2], k=1)[0]
            else:
                satisfaction = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2], k=1)[0]

            # Survey date: same day or 1-2 days after interaction
            survey_date = (interaction["interaction_date"] + timedelta(days=random.randint(0, 2))).date()

            # Comments (50% provide comments)
            comments = None
            if random.random() < 0.50:
                if satisfaction >= 4:
                    comments = random.choice([
                        "Great service!",
                        "Very helpful and professional.",
                        "Quick resolution, thank you.",
                        "Excellent customer service.",
                    ])
                elif satisfaction == 3:
                    comments = random.choice([
                        "Service was okay.",
                        "Could be better.",
                        "Average experience.",
                    ])
                else:
                    comments = random.choice([
                        "Long wait time.",
                        "Issue not fully resolved.",
                        "Disappointed with the service.",
                        "Expected better.",
                    ])

            survey = {
                "customer_id": interaction["customer_id"],
                "interaction_id": interaction["interaction_id"],
                "nps_score": nps_score,
                "satisfaction_rating": satisfaction,
                "survey_date": survey_date,
                "comments": comments,
            }

            surveys.append(survey)

        return surveys

    def generate_complaints(self, customers: list[dict]) -> list[dict]:
        """Generate complaints (8% of customers file complaints)."""
        complaints = []

        # 8% of customers file complaints
        complaining_customers = random.sample(customers, k=int(len(customers) * 0.08))

        for customer in complaining_customers:
            complaint_id = f"CMP-{uuid.uuid4().hex[:12].upper()}"

            complaint_type = CustomerGenerator._weighted_choice(self.COMPLAINT_TYPES)
            status = CustomerGenerator._weighted_choice(self.COMPLAINT_STATUS)
            priority = CustomerGenerator._weighted_choice(self.PRIORITY)

            # Filed date: between customer creation and now
            customer_created = customer["created_at"]
            days_since = (datetime.now() - customer_created).days
            if days_since > 0:
                random_days = random.randint(0, days_since)
                filed_date = customer_created + timedelta(days=random_days)
            else:
                filed_date = customer_created

            # Resolved date and resolution time (if status is resolved or closed)
            resolved_date = None
            resolution_time_hours = None
            if status in ["resolved", "closed"]:
                resolution_hours = random.randint(1, 168)  # 1 hour to 1 week
                resolved_date = filed_date + timedelta(hours=resolution_hours)
                resolution_time_hours = resolution_hours

            # Assigned to (90% assigned)
            assigned_to = None
            if random.random() < 0.90 and self.id_manager.employee_ids:
                assigned_to = random.choice(self.id_manager.employee_ids)

            # Description
            descriptions = {
                "service": [
                    "Poor customer service experience",
                    "Long wait times at branch",
                    "Unhelpful support staff",
                ],
                "fee": [
                    "Unexpected fees charged",
                    "Fee disclosure issue",
                    "Incorrect fee amount",
                ],
                "product": [
                    "Product not as advertised",
                    "Issues with account features",
                    "Product defect",
                ],
                "fraud": [
                    "Suspicious transaction",
                    "Potential fraud detected",
                    "Unauthorized account access",
                ],
                "other": [
                    "General complaint",
                    "Miscellaneous issue",
                    "Other concern",
                ],
            }

            complaint = {
                "complaint_id": complaint_id,
                "customer_id": customer["customer_id"],
                "complaint_type": complaint_type,
                "description": random.choice(descriptions[complaint_type]),
                "status": status,
                "priority": priority,
                "filed_date": filed_date,
                "resolved_date": resolved_date,
                "resolution_time_hours": resolution_time_hours,
                "assigned_to": assigned_to,
            }

            complaints.append(complaint)

        return complaints

    def generate_campaigns(self) -> list[dict]:
        """Generate marketing campaigns (fixed number, 10-15 campaigns)."""
        campaigns = []
        num_campaigns = random.randint(10, 15)

        segments = ["retail", "premium", "corporate", "private_banking", "all"]

        campaign_names = [
            "Summer Savings Boost",
            "Premium Card Launch",
            "Mortgage Rate Special",
            "Student Account Promotion",
            "Retirement Planning Seminar",
            "Business Banking Growth",
            "Digital Banking Adoption",
            "Loan Refinance Campaign",
            "Investment Product Launch",
            "Holiday Season Rewards",
            "New Year Financial Goals",
            "Spring Home Equity Drive",
            "Back to School Savings",
            "Year-End Tax Planning",
            "Mobile App Feature Release",
        ]

        # Shuffle and take num_campaigns
        selected_names = random.sample(campaign_names, k=min(num_campaigns, len(campaign_names)))

        for i, name in enumerate(selected_names):
            campaign_id = f"CAM-{uuid.uuid4().hex[:10].upper()}"

            campaign_type = CustomerGenerator._weighted_choice(self.CAMPAIGN_TYPES)
            target_segment = random.choice(segments)

            # Campaign dates in the past year
            start_date = fake.date_between(start_date="-1y", end_date="-30d")
            end_date = start_date + timedelta(days=random.randint(14, 90))

            campaign = {
                "campaign_id": campaign_id,
                "campaign_name": name,
                "campaign_type": campaign_type,
                "start_date": start_date,
                "end_date": end_date,
                "target_segment": target_segment,
            }

            campaigns.append(campaign)
            self.id_manager.add_campaign(campaign_id)

        return campaigns

    def generate_campaign_responses(self, campaigns: list[dict], customers: list[dict]) -> list[dict]:
        """Generate campaign responses (~5% of customers respond to campaigns)."""
        responses = []

        # 5% of customers respond
        responding_customers = random.sample(customers, k=int(len(customers) * 0.05))

        for customer in responding_customers:
            # Each responding customer responds to 1-2 campaigns
            num_responses = random.choices([1, 2], weights=[0.7, 0.3], k=1)[0]
            customer_campaigns = random.sample(campaigns, k=min(num_responses, len(campaigns)))

            for campaign in customer_campaigns:
                response_type = CustomerGenerator._weighted_choice(self.RESPONSE_TYPES)

                # Converted: 30% for purchased, 5% for clicked, 1% for opened, 0% for unsubscribed
                if response_type == "purchased":
                    converted = random.random() < 0.30
                elif response_type == "clicked":
                    converted = random.random() < 0.05
                elif response_type == "opened":
                    converted = random.random() < 0.01
                else:  # unsubscribed
                    converted = False

                # Response date: between campaign start and end
                response_date = fake.date_between(
                    start_date=campaign["start_date"],
                    end_date=campaign["end_date"]
                )

                response = {
                    "campaign_id": campaign["campaign_id"],
                    "customer_id": customer["customer_id"],
                    "response_date": response_date,
                    "response_type": response_type,
                    "converted": converted,
                }

                responses.append(response)

        return responses
