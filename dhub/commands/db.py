"""Database management commands."""

import typer
from rich.console import Console
from rich.table import Table

from dhub.config import config
from dhub.db import get_db_connection, list_databases, test_connection

console = Console()
app = typer.Typer()


@app.command("list")
def list_all_databases():
    """List all available databases."""
    console.print("[bold]Fetching databases...[/bold]\n")

    databases = list_databases()

    if not databases:
        console.print("[yellow]Could not retrieve database list[/yellow]")
        return

    table = Table(title="Available Databases", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=5)
    table.add_column("Database Name", style="green")
    table.add_column("Type", style="blue")

    demo_dbs = config.DEMO_DATABASES

    for idx, db_name in enumerate(databases, 1):
        db_type = "Demo" if db_name in demo_dbs else "System"
        table.add_row(str(idx), db_name, db_type)

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(databases)} database(s)")
    console.print(f"[dim]Demo databases: {len([db for db in databases if db in demo_dbs])}[/dim]")


@app.command("test")
def test_db_connection(
    database: str = typer.Option(None, "--database", "-d", help="Database to test (default: all demo databases)"),
):
    """Test database connection(s)."""
    if database:
        # Test single database
        console.print(f"[bold]Testing connection to '{database}'...[/bold]")
        if test_connection(database):
            console.print(f"[bold green]✓[/bold green] Successfully connected to '{database}'!")
        else:
            console.print(f"[bold red]✗[/bold red] Failed to connect to '{database}'")
            raise typer.Exit(code=1)
    else:
        # Test all demo databases
        console.print("[bold]Testing connections to all demo databases...[/bold]\n")
        results = []

        for db in config.DEMO_DATABASES:
            success = test_connection(db)
            results.append((db, success))
            status = "[green]✓[/green]" if success else "[red]✗[/red]"
            console.print(f"{status} {db}")

        successful = sum(1 for _, success in results if success)
        total = len(results)

        console.print(f"\n[bold]Results:[/bold] {successful}/{total} databases accessible")

        if successful < total:
            raise typer.Exit(code=1)


@app.command("tables")
def list_tables(
    database: str = typer.Option(None, "--database", "-d", help="Database to query (default: all demo databases)"),
    all_dbs: bool = typer.Option(False, "--all", help="Show tables from all databases"),
):
    """List all tables in the database(s)."""
    databases_to_query = []

    if database:
        # Query single database
        databases_to_query = [database]
    elif all_dbs:
        # Query all available databases
        databases_to_query = list_databases()
    else:
        # Query all demo databases (default)
        databases_to_query = config.DEMO_DATABASES

    console.print(f"[bold]Fetching tables from {len(databases_to_query)} database(s)...[/bold]\n")

    all_tables = []

    for db_name in databases_to_query:
        try:
            with get_db_connection(db_name) as conn:
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

                    for row in tables:
                        all_tables.append({
                            "database": db_name,
                            "schema": row["table_schema"],
                            "table": row["table_name"],
                            "type": row["table_type"],
                        })
        except Exception as e:
            console.print(f"[yellow]Warning: Could not query database '{db_name}': {e}[/yellow]")
            continue

    if not all_tables:
        console.print("[yellow]No tables found in the specified database(s)[/yellow]")
        return

    table = Table(title="Database Tables", show_header=True, header_style="bold cyan")
    table.add_column("Database", style="magenta")
    table.add_column("Schema", style="green")
    table.add_column("Table Name", style="blue")
    table.add_column("Type", style="yellow")

    for row in all_tables:
        table.add_row(row["database"], row["schema"], row["table"], row["type"])

    console.print(table)

    # Show summary by database
    db_counts = {}
    for row in all_tables:
        db_counts[row["database"]] = db_counts.get(row["database"], 0) + 1

    console.print(f"\n[bold]Total:[/bold] {len(all_tables)} table(s) across {len(db_counts)} database(s)")
    for db_name, count in sorted(db_counts.items()):
        console.print(f"  [cyan]{db_name}:[/cyan] {count} table(s)")


@app.command("query")
def execute_query(
    query: str = typer.Argument(..., help="SQL query to execute"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum rows to display"),
    database: str = typer.Option(None, "--database", "-d", help="Database to query"),
):
    """Execute a SQL query and display results."""
    db_name = database or config.POSTGRES_DB
    console.print(f"[bold]Executing query on '{db_name}'...[/bold]\n")
    console.print(f"[dim]{query}[/dim]\n")

    with get_db_connection(database) as conn:
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
def database_info(
    database: str = typer.Option(None, "--database", "-d", help="Database to get info for"),
):
    """Display database information."""
    db_name = database or config.POSTGRES_DB
    console.print(f"[bold]Database Information: {db_name}[/bold]\n")

    with get_db_connection(database) as conn:
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
