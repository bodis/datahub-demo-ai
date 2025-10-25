"""Data generation commands using Faker."""

import typer
from faker import Faker
from rich.console import Console
from rich.progress import track
from rich.table import Table

from dhub.db import get_db_connection

console = Console()
app = typer.Typer()
fake = Faker()


@app.command("users")
def generate_users(
    count: int = typer.Argument(10, help="Number of users to generate"),
    create_table: bool = typer.Option(False, "--create-table", help="Create users table if it doesn't exist"),
    insert: bool = typer.Option(False, "--insert", help="Insert generated data into database"),
):
    """Generate fake user data."""
    console.print(f"[bold]Generating {count} fake users...[/bold]\n")

    users = []
    for _ in track(range(count), description="Generating users..."):
        users.append({
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "address": fake.address().replace("\n", ", "),
            "company": fake.company(),
            "job_title": fake.job(),
        })

    table = Table(title="Generated Users", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Phone", style="yellow")
    table.add_column("Company", style="magenta")

    for user in users[:10]:
        table.add_row(user["name"], user["email"], user["phone"], user["company"])

    console.print(table)

    if count > 10:
        console.print(f"\n[dim]Showing first 10 of {count} users[/dim]")

    if insert:
        console.print("\n[bold]Inserting users into database...[/bold]")

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if create_table:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255),
                            email VARCHAR(255),
                            phone VARCHAR(50),
                            address TEXT,
                            company VARCHAR(255),
                            job_title VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    console.print("[green]✓[/green] Table 'users' created/verified")

                for user in users:
                    cur.execute("""
                        INSERT INTO users (name, email, phone, address, company, job_title)
                        VALUES (%(name)s, %(email)s, %(phone)s, %(address)s, %(company)s, %(job_title)s)
                    """, user)

                conn.commit()

        console.print(f"[bold green]✓[/bold green] Inserted {count} users into database")


@app.command("companies")
def generate_companies(
    count: int = typer.Argument(10, help="Number of companies to generate"),
    show_details: bool = typer.Option(False, "--details", help="Show detailed company information"),
):
    """Generate fake company data."""
    console.print(f"[bold]Generating {count} fake companies...[/bold]\n")

    companies = []
    for _ in track(range(count), description="Generating companies..."):
        companies.append({
            "name": fake.company(),
            "industry": fake.bs(),
            "email": fake.company_email(),
            "phone": fake.phone_number(),
            "website": fake.url(),
            "address": fake.address().replace("\n", ", "),
        })

    table = Table(title="Generated Companies", show_header=True, header_style="bold cyan")
    table.add_column("Company Name", style="green")
    table.add_column("Industry", style="blue")
    table.add_column("Email", style="yellow")

    if show_details:
        table.add_column("Phone", style="magenta")
        table.add_column("Website", style="cyan")

    for company in companies:
        row = [company["name"], company["industry"], company["email"]]
        if show_details:
            row.extend([company["phone"], company["website"]])
        table.add_row(*row)

    console.print(table)


@app.command("addresses")
def generate_addresses(
    count: int = typer.Argument(10, help="Number of addresses to generate"),
    locale: str = typer.Option("en_US", "--locale", "-l", help="Locale for address generation"),
):
    """Generate fake addresses."""
    fake_locale = Faker(locale)
    console.print(f"[bold]Generating {count} fake addresses ({locale})...[/bold]\n")

    addresses = []
    for _ in track(range(count), description="Generating addresses..."):
        addresses.append({
            "street": fake_locale.street_address(),
            "city": fake_locale.city(),
            "state": fake_locale.state(),
            "zipcode": fake_locale.postcode(),
            "country": fake_locale.country(),
        })

    table = Table(title="Generated Addresses", show_header=True, header_style="bold cyan")
    table.add_column("Street", style="green")
    table.add_column("City", style="blue")
    table.add_column("State", style="yellow")
    table.add_column("Zip", style="magenta")
    table.add_column("Country", style="cyan")

    for addr in addresses:
        table.add_row(addr["street"], addr["city"], addr["state"], addr["zipcode"], addr["country"])

    console.print(table)


@app.command("custom")
def generate_custom(
    field_type: str = typer.Argument(..., help="Faker method name (e.g., 'name', 'email', 'sentence')"),
    count: int = typer.Option(10, "--count", "-c", help="Number of items to generate"),
):
    """Generate custom fake data using any Faker method."""
    console.print(f"[bold]Generating {count} '{field_type}' values...[/bold]\n")

    try:
        faker_method = getattr(fake, field_type)
    except AttributeError:
        console.print(f"[bold red]Error:[/bold red] Unknown Faker method '{field_type}'")
        console.print("\n[yellow]Try one of these:[/yellow] name, email, address, phone_number, company, sentence, paragraph, url, color_name, etc.")
        raise typer.Exit(code=1)

    values = []
    for _ in track(range(count), description=f"Generating {field_type}..."):
        values.append(faker_method())

    table = Table(title=f"Generated {field_type.title()} Values", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=5)
    table.add_column("Value", style="green")

    for i, value in enumerate(values, 1):
        table.add_row(str(i), str(value))

    console.print(table)
