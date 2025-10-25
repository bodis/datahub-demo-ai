"""Data seeding commands for demo databases."""

import typer
from rich.console import Console

from dhub.data_generators.orchestrator import DataOrchestrator

console = Console()
app = typer.Typer()


@app.command("all")
def seed_all_databases(
    scale: float = typer.Option(
        1.0,
        "--scale",
        "-s",
        help="Scale factor for dataset sizes (0.1=demo, 1.0=base requirements, 5.0=large)",
    ),
    customers: int | None = typer.Option(
        None, "--customers", "-c", help="Override customer count (overrides scale)"
    ),
    employees: int | None = typer.Option(
        None, "--employees", "-e", help="Override employee count (overrides scale)"
    ),
):
    """
    Generate demo data for all databases with realistic relationships.

    Scale Factor Examples:
    - 0.1: Demo/Test (~120 customers, ~15 employees)
    - 1.0: Base Requirements (~1200 customers, ~150 employees)
    - 5.0: Large Enterprise (~6000 customers, ~750 employees)

    Generated Data (Phase 1-2 only):
    - Employees (with departments, roles, hierarchy)
    - Customers (master records + CRM profiles)
    - Accounts (checking, savings, etc.)

    All data maintains referential integrity across databases.

    Note: Departments, training programs, and branch codes are fixed
    and do not scale.
    """
    try:
        orchestrator = DataOrchestrator(
            scale_factor=scale, num_customers=customers, num_employees=employees
        )
        orchestrator.generate_all()

    except KeyboardInterrupt:
        console.print("\n[yellow]Data generation cancelled by user[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n[bold red]Error during data generation:[/bold red] {e}")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(code=1)


@app.command("clear")
def clear_all_databases(
    confirm: bool = typer.Option(False, "--confirm", help="Confirm deletion of all data"),
):
    """
    Clear all data from demo databases.

    WARNING: This will delete all generated data!
    """
    if not confirm:
        console.print("[yellow]This will delete ALL data from the demo databases![/yellow]")
        console.print("Use --confirm to proceed")
        raise typer.Exit(code=1)

    from dhub.config import config
    from dhub.db import get_db_connection

    databases = config.DEMO_DATABASES

    console.print("[bold]Clearing data from all databases...[/bold]\n")

    for db_name in databases:
        try:
            console.print(f"  Clearing {db_name}...")

            with get_db_connection(db_name) as conn:
                with conn.cursor() as cur:
                    # Get all tables
                    cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                    """)
                    tables = [row["table_name"] for row in cur.fetchall()]

                    # Truncate all tables
                    for table in tables:
                        cur.execute(f"TRUNCATE TABLE {table} CASCADE")

                    conn.commit()
                    console.print(f"  [green]✓[/green] Cleared {len(tables)} tables from {db_name}")

        except Exception as e:
            console.print(f"  [red]Error clearing {db_name}: {e}[/red]")

    console.print("\n[bold green]✓ All databases cleared![/bold green]")


@app.command("status")
def show_data_status():
    """Show current data counts in all demo databases."""
    from dhub.config import config
    from dhub.db import get_db_connection
    from rich.table import Table

    console.print("[bold]Demo Database Status[/bold]\n")

    databases = config.DEMO_DATABASES

    for db_name in databases:
        try:
            with get_db_connection(db_name) as conn:
                with conn.cursor() as cur:
                    # Get all tables with counts
                    cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    tables = [row["table_name"] for row in cur.fetchall()]

                    if tables:
                        table = Table(title=db_name, show_header=True, header_style="bold cyan")
                        table.add_column("Table", style="green")
                        table.add_column("Count", justify="right", style="yellow")

                        total_records = 0
                        for table_name in tables:
                            cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                            count = cur.fetchone()["count"]
                            total_records += count
                            table.add_row(table_name, str(count))

                        table.add_section()
                        table.add_row("[bold]Total[/bold]", f"[bold]{total_records}[/bold]")

                        console.print(table)
                        console.print()

        except Exception as e:
            console.print(f"[red]Error querying {db_name}: {e}[/red]\n")
