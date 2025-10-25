"""Database connection utilities."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import psycopg
import typer
from dotenv import load_dotenv
from psycopg.rows import dict_row
from rich.console import Console

from dhub.config import config

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

console = Console()


def get_connection_string(database: str | None = None) -> str:
    """Get PostgreSQL connection string from environment or use defaults.

    Args:
        database: Database name. If None, uses default from config.
    """
    return config.get_postgres_connection_string(database)


@contextmanager
def get_db_connection(database: str | None = None) -> Generator[psycopg.Connection, None, None]:
    """Context manager for database connections.

    Args:
        database: Database name. If None, uses default from config.
    """
    conn_string = get_connection_string(database)

    try:
        with psycopg.connect(conn_string, row_factory=dict_row) as conn:
            yield conn
    except psycopg.OperationalError as e:
        db_name = database or config.POSTGRES_DB
        console.print(f"[bold red]Error:[/bold red] Failed to connect to database")
        console.print(f"[red]{e}[/red]")
        console.print(f"\n[yellow]Connection details:[/yellow]")
        console.print(f"  Host: {config.POSTGRES_HOST}")
        console.print(f"  Port: {config.POSTGRES_PORT}")
        console.print(f"  Database: {db_name}")
        console.print(f"  User: {config.POSTGRES_USER}")
        console.print(f"\n[dim]Check your .env file or ensure PostgreSQL is running[/dim]")
        raise typer.Exit(code=1)


def test_connection(database: str | None = None) -> bool:
    """Test database connection.

    Args:
        database: Database name. If None, uses default from config.
    """
    try:
        with get_db_connection(database) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception:
        return False


def list_databases() -> list[str]:
    """List all available databases on the PostgreSQL server."""
    try:
        # Connect to default postgres database to list all databases
        with get_db_connection("postgres") as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT datname
                    FROM pg_database
                    WHERE datistemplate = false
                    ORDER BY datname
                """)
                results = cur.fetchall()
                return [row["datname"] for row in results]
    except Exception:
        return []
