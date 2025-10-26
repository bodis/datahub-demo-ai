"""Data generation orchestrator."""

import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import psycopg

from dhub.config import config
from dhub.data_generators.customers import AccountGenerator, CRMGenerator, CustomerGenerator
from dhub.data_generators.employees import EmployeeGenerator
from dhub.data_generators.id_manager import IDManager
from dhub.db import get_db_connection

console = Console()


class DataOrchestrator:
    """Orchestrates data generation across all databases."""

    # Base targets from requirements (scale_factor = 1.0)
    BASE_EMPLOYEES = 150
    BASE_CUSTOMERS = 1200

    # Fixed datasets (don't scale)
    FIXED_DEPARTMENTS = 12
    FIXED_TRAINING_PROGRAMS_RANGE = (20, 30)
    FIXED_BRANCH_CODES = 20

    def __init__(
        self,
        scale_factor: float = 1.0,
        num_customers: int | None = None,
        num_employees: int | None = None,
    ):
        """Initialize orchestrator.

        Args:
            scale_factor: Multiplier for dataset sizes (default: 1.0 = base requirements)
            num_customers: Override customer count (if None, uses BASE_CUSTOMERS * scale_factor)
            num_employees: Override employee count (if None, uses BASE_EMPLOYEES * scale_factor)
        """
        self.id_manager = IDManager()
        self.scale_factor = scale_factor

        # Calculate scaled sizes
        if num_customers is None:
            self.num_customers = int(self.BASE_CUSTOMERS * scale_factor)
        else:
            self.num_customers = num_customers

        if num_employees is None:
            self.num_employees = int(self.BASE_EMPLOYEES * scale_factor)
        else:
            self.num_employees = num_employees

        # Store generated data for validation
        self.generated_data = {}

        # Log configuration
        console.print(f"\n[dim]Configuration:[/dim]")
        console.print(f"  Scale Factor: [cyan]{scale_factor}[/cyan]")
        console.print(f"  Employees: [yellow]{self.num_employees}[/yellow] (base: {self.BASE_EMPLOYEES})")
        console.print(f"  Customers: [yellow]{self.num_customers}[/yellow] (base: {self.BASE_CUSTOMERS})")

    def _execute_with_retry(self, func, max_retries: int = 3, retry_delay: float = 1.0):
        """Execute a function with retry logic for database constraint violations.

        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Result from the function

        Raises:
            Exception: If all retries are exhausted
        """
        for attempt in range(max_retries):
            try:
                return func()
            except psycopg.errors.UniqueViolation as e:
                if attempt < max_retries - 1:
                    console.print(
                        f"  [yellow]⚠[/yellow] Unique constraint violation detected (attempt {attempt + 1}/{max_retries})"
                    )
                    console.print(f"  [dim]Error: {str(e).split(chr(10))[0]}[/dim]")
                    console.print(f"  [dim]Retrying in {retry_delay}s...[/dim]")
                    time.sleep(retry_delay)
                    # Reset generators for retry
                    self.id_manager = IDManager()
                    self.generated_data = {}
                else:
                    console.print(f"  [red]✗[/red] Failed after {max_retries} attempts")
                    raise
            except Exception as e:
                # For non-constraint errors, fail immediately
                console.print(f"  [red]✗[/red] Unexpected error: {type(e).__name__}")
                raise

    def generate_all(self) -> None:
        """Generate all data across databases."""
        console.print("\n[bold cyan]DataHub Demo Data Generation[/bold cyan]")
        console.print("=" * 60)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Phase 1: Foundation Data
            console.print("\n[bold]Phase 1: Foundation Data[/bold]")

            task = progress.add_task("Generating employees...", total=None)
            employees_data = self._generate_employees()
            progress.remove_task(task)

            task = progress.add_task("Generating customers...", total=None)
            customers_data = self._generate_customers()
            progress.remove_task(task)

            # Phase 2: Core Banking
            console.print("\n[bold]Phase 2: Core Banking Products[/bold]")

            task = progress.add_task("Generating accounts...", total=None)
            accounts_data = self._generate_accounts(customers_data["master"])
            progress.remove_task(task)

            # Phase 3: CRM Data
            console.print("\n[bold]Phase 3: CRM & Customer Engagement[/bold]")

            task = progress.add_task("Generating CRM data...", total=None)
            crm_data = self._generate_crm(customers_data["master"])
            progress.remove_task(task)

        # Show summary
        self._show_summary()

    def _generate_employees(self) -> dict:
        """Generate employee data with retry logic."""
        def _do_generate():
            emp_gen = EmployeeGenerator(self.id_manager, self.num_employees)

            # Generate departments
            departments = emp_gen.generate_departments()
            console.print(f"  [green]✓[/green] Generated {len(departments)} departments")

            # Insert departments
            with get_db_connection("employees_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO departments (department_id, department_name, department_head_id, budget)
                        VALUES (%(department_id)s, %(department_name)s, %(department_head_id)s, %(budget)s)
                    """, departments)
                    conn.commit()

            # Generate employees
            employees = emp_gen.generate_employees()
            console.print(f"  [green]✓[/green] Generated {len(employees)} employees")

            # Insert employees
            with get_db_connection("employees_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO employees (
                            employee_id, employee_number, first_name, last_name, email, phone,
                            role, department, branch_code, manager_id, hire_date,
                            termination_date, employment_status, salary
                        )
                        VALUES (
                            %(employee_id)s, %(employee_number)s, %(first_name)s, %(last_name)s,
                            %(email)s, %(phone)s, %(role)s, %(department)s, %(branch_code)s,
                            %(manager_id)s, %(hire_date)s, %(termination_date)s,
                            %(employment_status)s, %(salary)s
                        )
                    """, employees)
                    conn.commit()

            # Generate training programs
            programs = emp_gen.generate_training_programs()
            console.print(f"  [green]✓[/green] Generated {len(programs)} training programs")

            with get_db_connection("employees_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO training_programs (
                            program_id, program_name, description, duration_hours
                        )
                        VALUES (%(program_id)s, %(program_name)s, %(description)s, %(duration_hours)s)
                    """, programs)
                    conn.commit()

            return {"departments": departments, "employees": employees, "programs": programs}

        return self._execute_with_retry(_do_generate)

    def _generate_customers(self) -> dict:
        """Generate customer data with retry logic."""
        def _do_generate():
            cust_gen = CustomerGenerator(self.id_manager, self.num_customers)

            # Generate customer master (accounts_db)
            customers = cust_gen.generate_customers_master()
            console.print(f"  [green]✓[/green] Generated {len(customers)} customers (master)")

            # Insert into accounts_db (simpler schema)
            with get_db_connection("accounts_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO customers (
                            customer_id, first_name, last_name, date_of_birth, email, phone, created_at
                        )
                        VALUES (
                            %(customer_id)s, %(first_name)s, %(last_name)s, %(date_of_birth)s,
                            %(email)s, %(phone)s, %(created_at)s
                        )
                    """, customers)
                    conn.commit()

            # Generate customer profiles (customer_db)
            profiles = cust_gen.generate_customer_profiles(customers)
            console.print(f"  [green]✓[/green] Generated {len(profiles)} customer profiles (CRM)")

            # Insert into customer_db
            with get_db_connection("customer_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO customer_profiles (
                            customer_id, full_name, email, phone, address, city, country,
                            customer_segment, customer_status, onboarding_date, assigned_agent_id,
                            kyc_status, risk_rating, created_at, updated_at
                        )
                        VALUES (
                            %(customer_id)s, %(full_name)s, %(email)s, %(phone)s, %(address)s,
                            %(city)s, %(country)s, %(customer_segment)s, %(customer_status)s,
                            %(onboarding_date)s, %(assigned_agent_id)s, %(kyc_status)s,
                            %(risk_rating)s, %(created_at)s, %(updated_at)s
                        )
                    """, profiles)
                    conn.commit()

            return {"master": customers, "profiles": profiles}

        return self._execute_with_retry(_do_generate)

    def _generate_accounts(self, customers: list[dict]) -> dict:
        """Generate account data."""
        acc_gen = AccountGenerator(self.id_manager)

        # Generate accounts
        accounts = acc_gen.generate_accounts(customers)
        console.print(f"  [green]✓[/green] Generated {len(accounts)} accounts")

        # Insert into accounts_db
        with get_db_connection("accounts_db") as conn:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO accounts (
                        account_id, account_number, customer_id, account_type,
                        account_status, balance, currency, opened_date
                    )
                    VALUES (
                        %(account_id)s, %(account_number)s, %(customer_id)s,
                        %(account_type)s, %(status)s, %(balance)s, %(currency)s,
                        %(opened_date)s
                    )
                """, accounts)
                conn.commit()

        # Generate account relationships
        relationships = acc_gen.generate_account_relationships(accounts)
        console.print(f"  [green]✓[/green] Generated {len(relationships)} account relationships")

        # Insert relationships
        if relationships:
            with get_db_connection("accounts_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO account_relationships (
                            primary_account_id, related_account_id, relationship_type, created_at
                        )
                        VALUES (
                            %(primary_account_id)s, %(related_account_id)s,
                            %(relationship_type)s, %(created_at)s
                        )
                    """, relationships)
                    conn.commit()

        # Generate transactions
        transactions = acc_gen.generate_transactions(accounts)
        console.print(f"  [green]✓[/green] Generated {len(transactions)} transactions")

        # Insert transactions in batches (for performance)
        batch_size = 1000
        if transactions:
            with get_db_connection("accounts_db") as conn:
                with conn.cursor() as cur:
                    for i in range(0, len(transactions), batch_size):
                        batch = transactions[i:i + batch_size]
                        cur.executemany("""
                            INSERT INTO transactions (
                                transaction_id, account_id, transaction_type, transaction_amount,
                                transaction_date, description, balance_after,
                                counterparty_account, processed_by
                            )
                            VALUES (
                                %(transaction_id)s, %(account_id)s, %(transaction_type)s,
                                %(transaction_amount)s, %(transaction_date)s, %(description)s,
                                %(balance_after)s, %(counterparty_account)s, %(processed_by)s
                            )
                        """, batch)
                    conn.commit()

        return {"accounts": accounts, "relationships": relationships, "transactions": transactions}

    def _generate_crm(self, customers: list[dict]) -> dict:
        """Generate CRM data for customer_db."""
        crm_gen = CRMGenerator(self.id_manager, self.scale_factor)

        # Generate campaigns first (fixed, not customer-dependent)
        campaigns = crm_gen.generate_campaigns()
        console.print(f"  [green]✓[/green] Generated {len(campaigns)} marketing campaigns")

        # Insert campaigns
        with get_db_connection("customer_db") as conn:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO campaigns (
                        campaign_id, campaign_name, campaign_type, start_date, end_date, target_segment
                    )
                    VALUES (
                        %(campaign_id)s, %(campaign_name)s, %(campaign_type)s,
                        %(start_date)s, %(end_date)s, %(target_segment)s
                    )
                """, campaigns)
                conn.commit()

        # Generate interactions
        interactions = crm_gen.generate_interactions(customers)
        console.print(f"  [green]✓[/green] Generated {len(interactions)} customer interactions")

        # Insert interactions
        if interactions:
            with get_db_connection("customer_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO interactions (
                            interaction_id, customer_id, interaction_type, channel,
                            interaction_date, duration_minutes, notes, handled_by, outcome
                        )
                        VALUES (
                            %(interaction_id)s, %(customer_id)s, %(interaction_type)s,
                            %(channel)s, %(interaction_date)s, %(duration_minutes)s,
                            %(notes)s, %(handled_by)s, %(outcome)s
                        )
                    """, interactions)
                    conn.commit()

        # Generate satisfaction surveys
        surveys = crm_gen.generate_satisfaction_surveys(interactions, customers)
        console.print(f"  [green]✓[/green] Generated {len(surveys)} satisfaction surveys")

        # Insert surveys
        if surveys:
            with get_db_connection("customer_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO satisfaction_surveys (
                            customer_id, interaction_id, nps_score, satisfaction_rating,
                            survey_date, comments
                        )
                        VALUES (
                            %(customer_id)s, %(interaction_id)s, %(nps_score)s,
                            %(satisfaction_rating)s, %(survey_date)s, %(comments)s
                        )
                    """, surveys)
                    conn.commit()

        # Generate complaints
        complaints = crm_gen.generate_complaints(customers)
        console.print(f"  [green]✓[/green] Generated {len(complaints)} customer complaints")

        # Insert complaints
        if complaints:
            with get_db_connection("customer_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO complaints (
                            complaint_id, customer_id, complaint_type, description,
                            status, priority, filed_date, resolved_date,
                            resolution_time_hours, assigned_to
                        )
                        VALUES (
                            %(complaint_id)s, %(customer_id)s, %(complaint_type)s,
                            %(description)s, %(status)s, %(priority)s, %(filed_date)s,
                            %(resolved_date)s, %(resolution_time_hours)s, %(assigned_to)s
                        )
                    """, complaints)
                    conn.commit()

        # Generate campaign responses
        responses = crm_gen.generate_campaign_responses(campaigns, customers)
        console.print(f"  [green]✓[/green] Generated {len(responses)} campaign responses")

        # Insert responses
        if responses:
            with get_db_connection("customer_db") as conn:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO campaign_responses (
                            campaign_id, customer_id, response_date, response_type, converted
                        )
                        VALUES (
                            %(campaign_id)s, %(customer_id)s, %(response_date)s,
                            %(response_type)s, %(converted)s
                        )
                    """, responses)
                    conn.commit()

        return {
            "campaigns": campaigns,
            "interactions": interactions,
            "surveys": surveys,
            "complaints": complaints,
            "responses": responses,
        }

    def _show_summary(self) -> None:
        """Show generation summary."""
        console.print("\n[bold green]✓ Data Generation Complete![/bold green]\n")

        stats = self.id_manager.get_stats()

        table = Table(title="Generated Records Summary", show_header=True, header_style="bold cyan")
        table.add_column("Category", style="green")
        table.add_column("Count", justify="right", style="yellow")

        table.add_row("Employees", str(stats["employees"]))
        table.add_row("  ├─ Loan Officers", str(stats["loan_officers"]))
        table.add_row("  ├─ Insurance Agents", str(stats["insurance_agents"]))
        table.add_row("  └─ Compliance Officers", str(stats["compliance_officers"]))
        table.add_row("Customers", str(stats["customers"]))
        table.add_row("Accounts", str(stats["accounts"]))

        console.print(table)

        # Show database-wise counts
        console.print("\n[bold]Database-wise Record Counts:[/bold]")
        self._show_database_counts()

    def _show_database_counts(self) -> None:
        """Show record counts per database."""
        databases = {
            "employees_db": ["departments", "employees", "training_programs"],
            "customer_db": ["customer_profiles", "interactions", "satisfaction_surveys", "complaints", "campaigns", "campaign_responses"],
            "accounts_db": ["customers", "accounts", "account_relationships", "transactions"],
        }

        for db_name, tables in databases.items():
            try:
                with get_db_connection(db_name) as conn:
                    with conn.cursor() as cur:
                        console.print(f"\n  [cyan]{db_name}:[/cyan]")
                        for table in tables:
                            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                            count = cur.fetchone()["count"]
                            console.print(f"    {table}: {count}")
            except Exception as e:
                console.print(f"  [red]Error querying {db_name}: {e}[/red]")
