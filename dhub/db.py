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

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

console = Console()


def get_connection_string() -> str:
    """Get PostgreSQL connection string from environment or use defaults."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    database = os.getenv("POSTGRES_DB", "mydb")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """Context manager for database connections."""
    conn_string = get_connection_string()

    try:
        with psycopg.connect(conn_string, row_factory=dict_row) as conn:
            yield conn
    except psycopg.OperationalError as e:
        console.print(f"[bold red]Error:[/bold red] Failed to connect to database")
        console.print(f"[red]{e}[/red]")
        console.print(f"\n[yellow]Connection details:[/yellow]")
        console.print(f"  Host: {os.getenv('POSTGRES_HOST', 'localhost')}")
        console.print(f"  Port: {os.getenv('POSTGRES_PORT', '5432')}")
        console.print(f"  Database: {os.getenv('POSTGRES_DB', 'mydb')}")
        console.print(f"  User: {os.getenv('POSTGRES_USER', 'postgres')}")
        console.print(f"\n[dim]Check your .env file or ensure PostgreSQL is running[/dim]")
        raise typer.Exit(code=1)


def test_connection() -> bool:
    """Test database connection."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception:
        return False
