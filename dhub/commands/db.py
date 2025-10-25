"""Database management commands."""

import typer
from rich.console import Console
from rich.table import Table

from dhub.db import get_db_connection, test_connection

console = Console()
app = typer.Typer()


@app.command("test")
def test_db_connection():
    """Test the database connection."""
    console.print("[bold]Testing database connection...[/bold]")

    if test_connection():
        console.print("[bold green]✓[/bold green] Successfully connected to the database!")
    else:
        console.print("[bold red]✗[/bold red] Failed to connect to the database")
        raise typer.Exit(code=1)


@app.command("tables")
def list_tables():
    """List all tables in the database."""
    console.print("[bold]Fetching tables...[/bold]\n")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    table_schema,
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
            """)
            tables = cur.fetchall()

    if not tables:
        console.print("[yellow]No tables found in the database[/yellow]")
        return

    table = Table(title="Database Tables", show_header=True, header_style="bold cyan")
    table.add_column("Schema", style="green")
    table.add_column("Table Name", style="blue")
    table.add_column("Type", style="magenta")

    for row in tables:
        table.add_row(row["table_schema"], row["table_name"], row["table_type"])

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(tables)} table(s)")


@app.command("query")
def execute_query(
    query: str = typer.Argument(..., help="SQL query to execute"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum rows to display"),
):
    """Execute a SQL query and display results."""
    console.print(f"[bold]Executing query...[/bold]\n")
    console.print(f"[dim]{query}[/dim]\n")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)

            if cur.description:
                rows = cur.fetchmany(limit)

                if not rows:
                    console.print("[yellow]Query returned no results[/yellow]")
                    return

                table = Table(show_header=True, header_style="bold cyan")

                for col in cur.description:
                    table.add_column(col.name)

                for row in rows:
                    table.add_row(*[str(val) for val in row.values()])

                console.print(table)
                console.print(f"\n[bold]Rows:[/bold] {len(rows)}{' (limited)' if len(rows) == limit else ''}")
            else:
                console.print("[green]Query executed successfully[/green]")


@app.command("info")
def database_info():
    """Display database information."""
    console.print("[bold]Database Information[/bold]\n")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()["version"]

            cur.execute("SELECT current_database()")
            db_name = cur.fetchone()["current_database"]

            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cur.fetchone()["pg_size_pretty"]

            cur.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            active_connections = cur.fetchone()["count"]

    info_table = Table(show_header=False, box=None)
    info_table.add_column(style="cyan bold")
    info_table.add_column(style="white")

    info_table.add_row("Database Name:", db_name)
    info_table.add_row("Database Size:", db_size)
    info_table.add_row("Active Connections:", str(active_connections))
    info_table.add_row("PostgreSQL Version:", version.split(",")[0])

    console.print(info_table)
