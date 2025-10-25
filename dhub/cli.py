"""Main CLI application entry point."""

import typer
from rich.console import Console

from dhub.commands import db, generate

console = Console()
app = typer.Typer(
    name="dhub",
    help="🚀 DHub - Beautiful CLI for database operations and data generation",
    add_completion=True,
    rich_markup_mode="rich",
)

# Register command groups
app.add_typer(db.app, name="db", help="📊 Database operations")
app.add_typer(generate.app, name="generate", help="🎲 Generate fake data")


@app.command()
def version():
    """Show the application version."""
    from dhub import __version__

    console.print(f"[bold cyan]DHub[/bold cyan] version [green]{__version__}[/green]")


@app.callback()
def main():
    """
    DHub CLI - Your companion for database operations and data generation.
    """
    pass


if __name__ == "__main__":
    app()
