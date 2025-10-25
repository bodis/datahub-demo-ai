"""ID management for cross-database relationships."""

from typing import Any


class IDManager:
    """Manages IDs across databases for referential integrity."""

    def __init__(self):
        """Initialize ID storage."""
        # Employees
        self.employee_ids: list[str] = []
        self.loan_officers: list[str] = []
        self.insurance_agents: list[str] = []
        self.compliance_officers: list[str] = []
        self.department_ids: list[str] = []

        # Customers
        self.customer_ids: list[str] = []

        # Accounts
        self.account_ids: list[str] = []
        self.customer_to_accounts: dict[str, list[str]] = {}

        # Loans
        self.loan_application_ids: list[str] = []
        self.approved_application_ids: list[str] = []
        self.loan_ids: list[str] = []

        # Insurance
        self.policy_ids: list[str] = []
        self.claim_ids: list[str] = []

        # Compliance
        self.aml_check_ids: list[str] = []
        self.sar_ids: list[str] = []
        self.rule_ids: list[str] = []

        # Campaigns
        self.campaign_ids: list[str] = []
        self.interaction_ids: list[str] = []

    def add_employee(self, employee_id: str, role: str) -> None:
        """Add an employee and categorize by role."""
        self.employee_ids.append(employee_id)

        if "loan" in role.lower() or "lending" in role.lower():
            self.loan_officers.append(employee_id)
        elif "insurance" in role.lower():
            self.insurance_agents.append(employee_id)
        elif "compliance" in role.lower():
            self.compliance_officers.append(employee_id)

    def add_customer(self, customer_id: str) -> None:
        """Add a customer ID."""
        self.customer_ids.append(customer_id)
        self.customer_to_accounts[customer_id] = []

    def add_account(self, account_id: str, customer_id: str) -> None:
        """Add an account and link to customer."""
        self.account_ids.append(account_id)
        if customer_id in self.customer_to_accounts:
            self.customer_to_accounts[customer_id].append(account_id)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about generated IDs."""
        return {
            "employees": len(self.employee_ids),
            "loan_officers": len(self.loan_officers),
            "insurance_agents": len(self.insurance_agents),
            "compliance_officers": len(self.compliance_officers),
            "customers": len(self.customer_ids),
            "accounts": len(self.account_ids),
            "loans": len(self.loan_ids),
            "policies": len(self.policy_ids),
        }
