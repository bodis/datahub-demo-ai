"""DataHub metadata import commands."""

import csv
import json
import requests
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import (
    ChangeTypeClass,
    DomainPropertiesClass,
    GlossaryTermInfoClass,
)

from dhub.config import config
from dhub.db import get_db_connection

app = typer.Typer(help="DataHub metadata import commands")
console = Console()


def make_domain_urn(domain_id: str) -> str:
    """Create DataHub domain URN."""
    return f"urn:li:domain:{domain_id}"


def make_glossary_term_urn(term_id: str) -> str:
    """Create DataHub glossary term URN."""
    return f"urn:li:glossaryTerm:{term_id}"


def make_tag_urn(tag: str) -> str:
    """Create DataHub tag URN."""
    return f"urn:li:tag:{tag}"


def get_datahub_emitter() -> DatahubRestEmitter:
    """Create and return DataHub REST emitter."""
    gms_server = config.get_datahub_url()
    token = config.DATAHUB_TOKEN if config.DATAHUB_TOKEN else None

    if token:
        return DatahubRestEmitter(gms_server=gms_server, token=token)
    else:
        return DatahubRestEmitter(gms_server=gms_server)


def find_csv_files(root_path: Path, filename: str) -> List[Path]:
    """Find all CSV files with the given filename in subdirectories.

    Args:
        root_path: Root directory to search
        filename: Name of CSV file to find (e.g., "domains.csv")

    Returns:
        List of Path objects for found CSV files
    """
    csv_files = []
    if not root_path.exists():
        console.print(f"[yellow]Warning: Import root path does not exist: {root_path}[/yellow]")
        return csv_files

    # Search in all subdirectories
    for subdir in root_path.iterdir():
        if subdir.is_dir():
            csv_path = subdir / filename
            if csv_path.exists():
                csv_files.append(csv_path)

    return csv_files


def read_domains_csv(csv_path: Path) -> List[Dict[str, str]]:
    """Read domains from CSV file.

    Expected columns: domain_id, parent_domain_id, name, description
    """
    domains = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domains.append({
                'domain_id': row['domain_id'].strip(),
                'parent_domain_id': row['parent_domain_id'].strip() if row['parent_domain_id'] else None,
                'name': row['name'].strip(),
                'description': row['description'].strip(),
            })
    return domains


def read_glossaries_csv(csv_path: Path) -> List[Dict[str, str]]:
    """Read glossary terms from CSV file.

    Expected columns: glossary_id, glossary_parent_id, name, definition, domain_id
    """
    terms = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            terms.append({
                'glossary_id': row['glossary_id'].strip(),
                'glossary_parent_id': row['glossary_parent_id'].strip() if row['glossary_parent_id'] else None,
                'name': row['name'].strip(),
                'definition': row['definition'].strip(),
                'domain_id': row.get('domain_id', '').strip() if row.get('domain_id') else None,
            })
    return terms


def sort_domains_by_hierarchy(domains: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Sort domains so parent domains are created before their children.

    Uses topological sort to handle arbitrary nesting levels.
    """
    # Build adjacency list
    children_map: Dict[Optional[str], List[Dict[str, str]]] = {}
    for domain in domains:
        parent = domain['parent_domain_id']
        if parent not in children_map:
            children_map[parent] = []
        children_map[parent].append(domain)

    # Topological sort (DFS)
    sorted_domains = []
    visited = set()

    def visit(domain_id: Optional[str]):
        if domain_id in visited:
            return
        visited.add(domain_id)

        # Visit children
        if domain_id in children_map:
            for child in children_map[domain_id]:
                visit(child['domain_id'])
                sorted_domains.append(child)

    # Start with root domains (no parent)
    visit(None)

    return sorted_domains


def sort_glossaries_by_hierarchy(terms: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Sort glossary terms so parent terms are created before their children.

    Uses topological sort to handle arbitrary nesting levels.
    """
    # Build adjacency list
    children_map: Dict[Optional[str], List[Dict[str, str]]] = {}
    for term in terms:
        parent = term['glossary_parent_id']
        if parent not in children_map:
            children_map[parent] = []
        children_map[parent].append(term)

    # Topological sort (DFS)
    sorted_terms = []
    visited = set()

    def visit(term_id: Optional[str]):
        if term_id in visited:
            return
        visited.add(term_id)

        # Visit children
        if term_id in children_map:
            for child in children_map[term_id]:
                visit(child['glossary_id'])
                sorted_terms.append(child)

    # Start with root terms (no parent)
    visit(None)

    return sorted_terms


def import_domain(emitter: DatahubRestEmitter, domain: Dict[str, str]) -> bool:
    """Import a single domain to DataHub.

    Returns True if successful, False otherwise.
    """
    try:
        domain_id = domain['domain_id']
        name = domain['name']
        description = domain['description']
        parent_domain_id = domain['parent_domain_id']

        # Create domain properties with parent domain if specified
        if parent_domain_id:
            domain_properties = DomainPropertiesClass(
                name=name,
                description=description,
                parentDomain=make_domain_urn(parent_domain_id),
            )
        else:
            domain_properties = DomainPropertiesClass(
                name=name,
                description=description,
            )

        # Create MCP
        mcp = MetadataChangeProposalWrapper(
            entityType="domain",
            changeType=ChangeTypeClass.UPSERT,
            entityUrn=make_domain_urn(domain_id),
            aspectName="domainProperties",
            aspect=domain_properties,
        )

        emitter.emit_mcp(mcp)

        return True
    except Exception as e:
        console.print(f"[red]Error importing domain {domain.get('domain_id', 'unknown')}: {e}[/red]")
        return False


def import_glossary_term(emitter: DatahubRestEmitter, term: Dict[str, str]) -> bool:
    """Import a single glossary term to DataHub.

    Returns True if successful, False otherwise.
    """
    try:
        glossary_id = term['glossary_id']
        name = term['name']
        definition = term['definition']
        parent_id = term['glossary_parent_id']
        domain_id = term['domain_id']

        # Create glossary term info
        term_info = GlossaryTermInfoClass(
            name=name,
            definition=definition,
            termSource="INTERNAL",
        )

        # Set parent term if exists
        if parent_id:
            term_info.parentTerm = make_glossary_term_urn(parent_id)

        # Create MCP
        mcp = MetadataChangeProposalWrapper(
            entityType="glossaryTerm",
            changeType=ChangeTypeClass.UPSERT,
            entityUrn=make_glossary_term_urn(glossary_id),
            aspectName="glossaryTermInfo",
            aspect=term_info,
        )

        emitter.emit_mcp(mcp)

        # Associate with domain if specified
        if domain_id:
            try:
                # Try to set domain association
                # Note: The relationship between glossary terms and domains is typically
                # managed through the domain aspect on the glossary term entity
                from datahub.metadata.schema_classes import DomainsClass

                domain_aspect = DomainsClass(
                    domains=[make_domain_urn(domain_id)]
                )

                domain_mcp = MetadataChangeProposalWrapper(
                    entityType="glossaryTerm",
                    changeType=ChangeTypeClass.UPSERT,
                    entityUrn=make_glossary_term_urn(glossary_id),
                    aspectName="domains",
                    aspect=domain_aspect,
                )

                emitter.emit_mcp(domain_mcp)
            except ImportError:
                console.print(f"[yellow]Warning: Domain association not set for {glossary_id} (DomainsClass not available)[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not associate domain for {glossary_id}: {e}[/yellow]")

        return True
    except Exception as e:
        console.print(f"[red]Error importing glossary term {term.get('glossary_id', 'unknown')}: {e}[/red]")
        return False


@app.command("import-domains")
def import_domains_command(
    subdirectory: Optional[str] = typer.Option(
        None,
        "--subdirectory",
        "-s",
        help="Specific subdirectory to import from (e.g., 'bank'). If not specified, imports from all subdirectories."
    ),
):
    """Import domains from CSV files into DataHub.

    Searches for domains.csv files in subdirectories under the imports root.
    Handles hierarchical domains by creating parent domains first.
    """
    console.print("[bold blue]DataHub Domain Import[/bold blue]\n")

    imports_root = config.get_imports_root()
    console.print(f"Import root: [cyan]{imports_root}[/cyan]")

    # Find CSV files
    if subdirectory:
        csv_path = imports_root / subdirectory / "domains.csv"
        csv_files = [csv_path] if csv_path.exists() else []
        if not csv_files:
            console.print(f"[red]Error: domains.csv not found in {imports_root / subdirectory}[/red]")
            raise typer.Exit(1)
    else:
        csv_files = find_csv_files(imports_root, "domains.csv")

    if not csv_files:
        console.print("[yellow]No domains.csv files found[/yellow]")
        raise typer.Exit(0)

    console.print(f"Found {len(csv_files)} domains.csv file(s)\n")

    # Create emitter
    try:
        emitter = get_datahub_emitter()
        console.print(f"[green]Connected to DataHub: {config.get_datahub_url()}[/green]\n")
    except Exception as e:
        console.print(f"[red]Failed to connect to DataHub: {e}[/red]")
        raise typer.Exit(1)

    # Process each CSV file
    total_imported = 0
    total_failed = 0

    for csv_path in csv_files:
        console.print(f"[bold]Processing: {csv_path.parent.name}/domains.csv[/bold]")

        try:
            # Read domains
            domains = read_domains_csv(csv_path)
            console.print(f"  Found {len(domains)} domain(s)")

            # Sort by hierarchy (parents first)
            sorted_domains = sort_domains_by_hierarchy(domains)

            # Import domains
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("  Importing domains...", total=len(sorted_domains))

                for domain in sorted_domains:
                    success = import_domain(emitter, domain)
                    if success:
                        total_imported += 1
                    else:
                        total_failed += 1
                    progress.advance(task)

            console.print(f"  [green]✓ Completed[/green]\n")

        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]\n")
            total_failed += len(domains) if 'domains' in locals() else 0

    # Summary
    console.print("\n[bold]Import Summary[/bold]")
    table = Table(show_header=False)
    table.add_row("Total imported:", f"[green]{total_imported}[/green]")
    table.add_row("Total failed:", f"[red]{total_failed}[/red]" if total_failed > 0 else "0")
    console.print(table)

    if total_imported > 0:
        console.print(f"\n[dim]View domains: {config.DATAHUB_FRONTEND_URL}/domains[/dim]")


@app.command("import-glossaries")
def import_glossaries_command(
    subdirectory: Optional[str] = typer.Option(
        None,
        "--subdirectory",
        "-s",
        help="Specific subdirectory to import from (e.g., 'bank'). If not specified, imports from all subdirectories."
    ),
):
    """Import glossary terms from CSV files into DataHub.

    Searches for glossaries.csv files in subdirectories under the imports root.
    Handles hierarchical glossary terms and domain associations.
    """
    console.print("[bold blue]DataHub Glossary Import[/bold blue]\n")

    imports_root = config.get_imports_root()
    console.print(f"Import root: [cyan]{imports_root}[/cyan]")

    # Find CSV files
    if subdirectory:
        csv_path = imports_root / subdirectory / "glossaries.csv"
        csv_files = [csv_path] if csv_path.exists() else []
        if not csv_files:
            console.print(f"[red]Error: glossaries.csv not found in {imports_root / subdirectory}[/red]")
            raise typer.Exit(1)
    else:
        csv_files = find_csv_files(imports_root, "glossaries.csv")

    if not csv_files:
        console.print("[yellow]No glossaries.csv files found[/yellow]")
        raise typer.Exit(0)

    console.print(f"Found {len(csv_files)} glossaries.csv file(s)\n")

    # Create emitter
    try:
        emitter = get_datahub_emitter()
        console.print(f"[green]Connected to DataHub: {config.get_datahub_url()}[/green]\n")
    except Exception as e:
        console.print(f"[red]Failed to connect to DataHub: {e}[/red]")
        raise typer.Exit(1)

    # Process each CSV file
    total_imported = 0
    total_failed = 0

    for csv_path in csv_files:
        console.print(f"[bold]Processing: {csv_path.parent.name}/glossaries.csv[/bold]")

        try:
            # Read glossary terms
            terms = read_glossaries_csv(csv_path)
            console.print(f"  Found {len(terms)} glossary term(s)")

            # Sort by hierarchy (parents first)
            sorted_terms = sort_glossaries_by_hierarchy(terms)

            # Import glossary terms
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("  Importing glossary terms...", total=len(sorted_terms))

                for term in sorted_terms:
                    success = import_glossary_term(emitter, term)
                    if success:
                        total_imported += 1
                    else:
                        total_failed += 1
                    progress.advance(task)

            console.print(f"  [green]✓ Completed[/green]\n")

        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]\n")
            total_failed += len(terms) if 'terms' in locals() else 0

    # Summary
    console.print("\n[bold]Import Summary[/bold]")
    table = Table(show_header=False)
    table.add_row("Total imported:", f"[green]{total_imported}[/green]")
    table.add_row("Total failed:", f"[red]{total_failed}[/red]" if total_failed > 0 else "0")
    console.print(table)

    if total_imported > 0:
        console.print(f"\n[dim]View glossary: {config.DATAHUB_FRONTEND_URL}/glossary[/dim]")


@app.command("import-all")
def import_all_command(
    subdirectory: Optional[str] = typer.Option(
        None,
        "--subdirectory",
        "-s",
        help="Specific subdirectory to import from (e.g., 'bank'). If not specified, imports from all subdirectories."
    ),
):
    """Import both domains and glossaries in the correct order.

    First imports domains, then glossaries (which can reference domains).
    """
    console.print("[bold blue]DataHub Metadata Import (All)[/bold blue]\n")

    # Import domains first
    console.print("[bold cyan]Step 1: Importing Domains[/bold cyan]")
    console.print("─" * 60)
    try:
        import_domains_command(subdirectory=subdirectory)
    except SystemExit:
        pass

    console.print("\n")

    # Import glossaries second
    console.print("[bold cyan]Step 2: Importing Glossaries[/bold cyan]")
    console.print("─" * 60)
    try:
        import_glossaries_command(subdirectory=subdirectory)
    except SystemExit:
        pass

    console.print("\n[green]✓ All imports completed[/green]")


def delete_entity(urn: str) -> bool:
    """Delete an entity from DataHub using REST API.

    Returns True if successful, False otherwise.
    """
    try:
        gms_url = config.get_datahub_url()
        token = config.DATAHUB_TOKEN if config.DATAHUB_TOKEN else None

        # URL encode the URN
        encoded_urn = quote(urn, safe='')

        # DataHub delete endpoint
        delete_url = f"{gms_url}/entities?action=delete"

        headers = {
            "Content-Type": "application/json",
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Send delete request with URN in body
        response = requests.post(
            delete_url,
            json={"urn": urn},
            headers=headers,
        )

        if response.status_code in [200, 204]:
            return True
        else:
            # Try alternative delete endpoint (older DataHub versions)
            delete_url_alt = f"{gms_url}/entities?urn={encoded_urn}"
            response = requests.delete(delete_url_alt, headers=headers)

            if response.status_code in [200, 204]:
                return True
            else:
                console.print(f"[red]Delete failed for {urn}: HTTP {response.status_code}[/red]")
                return False

    except Exception as e:
        console.print(f"[red]Error deleting entity {urn}: {e}[/red]")
        return False


def delete_glossary_term(term_id: str) -> bool:
    """Delete a single glossary term from DataHub.

    Returns True if successful, False otherwise.
    """
    urn = make_glossary_term_urn(term_id)
    return delete_entity(urn)


def delete_domain(domain_id: str) -> bool:
    """Delete a single domain from DataHub.

    Returns True if successful, False otherwise.
    """
    urn = make_domain_urn(domain_id)
    return delete_entity(urn)


def delete_tag(tag: str) -> bool:
    """Delete a single tag from DataHub.

    Returns True if successful, False otherwise.
    """
    urn = make_tag_urn(tag)
    return delete_entity(urn)


# Import helper modules for better organization
from dhub.commands.datahub_client import fetch_dataset_details
from dhub.commands.datahub_utils import parse_table_urn
from dhub.commands.datahub_display import (
    display_table_header,
    display_columns_table,
    display_column_statistics,
    print_yaml_output,
    display_summary,
)


# ============================================================================
# CLI Commands
# ============================================================================

@app.command("clear")
def clear_command(
    subdirectory: Optional[str] = typer.Option(
        None,
        "--subdirectory",
        "-s",
        help="Specific subdirectory to clear from (e.g., 'bank'). If not specified, clears from all subdirectories."
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm deletion (required to prevent accidental deletions)"
    ),
    include_tags: bool = typer.Option(
        False,
        "--tags",
        help="Also delete tags (note: tags are not stored in CSV files, so this is rarely needed)"
    ),
):
    """Delete domains and glossaries from DataHub based on CSV files.

    This command will delete all domains and glossaries found in the CSV files.
    Use with caution as this operation cannot be undone!

    Requires --confirm flag to execute.
    """
    if not confirm:
        console.print("[yellow]⚠️  Clear operation requires --confirm flag to proceed[/yellow]")
        console.print("[dim]Example: dhub datahub clear --confirm --subdirectory bank[/dim]")
        raise typer.Exit(1)

    console.print("[bold red]DataHub Metadata Clear[/bold red]\n")
    console.print("[yellow]⚠️  This will DELETE metadata from DataHub![/yellow]\n")

    imports_root = config.get_imports_root()
    console.print(f"Import root: [cyan]{imports_root}[/cyan]")

    # Create emitter
    try:
        emitter = get_datahub_emitter()
        console.print(f"[green]Connected to DataHub: {config.get_datahub_url()}[/green]\n")
    except Exception as e:
        console.print(f"[red]Failed to connect to DataHub: {e}[/red]")
        raise typer.Exit(1)

    total_deleted = 0
    total_failed = 0

    # Step 1: Delete glossaries (must be done before domains if they reference domains)
    console.print("[bold cyan]Step 1: Deleting Glossary Terms[/bold cyan]")
    console.print("─" * 60)

    if subdirectory:
        csv_path = imports_root / subdirectory / "glossaries.csv"
        glossary_files = [csv_path] if csv_path.exists() else []
    else:
        glossary_files = find_csv_files(imports_root, "glossaries.csv")

    if glossary_files:
        console.print(f"Found {len(glossary_files)} glossaries.csv file(s)")

        for csv_path in glossary_files:
            console.print(f"\n[bold]Processing: {csv_path.parent.name}/glossaries.csv[/bold]")

            try:
                terms = read_glossaries_csv(csv_path)
                console.print(f"  Found {len(terms)} glossary term(s) to delete")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("  Deleting glossary terms...", total=len(terms))

                    for term in terms:
                        success = delete_glossary_term(term['glossary_id'])
                        if success:
                            total_deleted += 1
                        else:
                            total_failed += 1
                        progress.advance(task)

                console.print(f"  [green]✓ Completed[/green]")

            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
                total_failed += len(terms) if 'terms' in locals() else 0
    else:
        console.print("[dim]No glossaries.csv files found[/dim]")

    # Step 2: Delete domains
    console.print("\n[bold cyan]Step 2: Deleting Domains[/bold cyan]")
    console.print("─" * 60)

    if subdirectory:
        csv_path = imports_root / subdirectory / "domains.csv"
        domain_files = [csv_path] if csv_path.exists() else []
    else:
        domain_files = find_csv_files(imports_root, "domains.csv")

    if domain_files:
        console.print(f"Found {len(domain_files)} domains.csv file(s)")

        for csv_path in domain_files:
            console.print(f"\n[bold]Processing: {csv_path.parent.name}/domains.csv[/bold]")

            try:
                domains = read_domains_csv(csv_path)
                console.print(f"  Found {len(domains)} domain(s) to delete")

                # Sort in reverse hierarchy (children first, then parents)
                sorted_domains = sort_domains_by_hierarchy(domains)
                sorted_domains.reverse()  # Reverse to delete children before parents

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("  Deleting domains...", total=len(sorted_domains))

                    for domain in sorted_domains:
                        success = delete_domain(domain['domain_id'])
                        if success:
                            total_deleted += 1
                        else:
                            total_failed += 1
                        progress.advance(task)

                console.print(f"  [green]✓ Completed[/green]")

            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
                total_failed += len(domains) if 'domains' in locals() else 0
    else:
        console.print("[dim]No domains.csv files found[/dim]")

    # Step 3: Delete tags (optional, rarely needed)
    if include_tags:
        console.print("\n[bold cyan]Step 3: Deleting Tags[/bold cyan]")
        console.print("─" * 60)
        console.print("[yellow]Note: Tags are not tracked in CSV files.[/yellow]")
        console.print("[yellow]Use DataHub UI to manage tags.[/yellow]")

    # Summary
    console.print("\n[bold]Clear Summary[/bold]")
    table = Table(show_header=False)
    table.add_row("Total deleted:", f"[green]{total_deleted}[/green]")
    table.add_row("Total failed:", f"[red]{total_failed}[/red]" if total_failed > 0 else "0")
    console.print(table)

    console.print("\n[green]✓ Clear operation completed[/green]")


# =============================================================================
# Database Ingestion Commands
# =============================================================================

DATABASE_LIST = [
    "employees_db",
    "customer_db",
    "accounts_db",
    "insurance_db",
    "loans_db",
    "compliance_db",
]


def get_postgres_config(database: str) -> Dict[str, str]:
    """Get PostgreSQL connection configuration for a specific database.

    Args:
        database: The database name to connect to

    Returns:
        Dictionary with connection parameters
    """
    return {
        "host": config.POSTGRES_HOST,
        "port": str(config.POSTGRES_PORT),
        "database": database,
        "username": config.POSTGRES_USER,
        "password": config.POSTGRES_PASSWORD,
    }


def generate_ingestion_config(
    database_name: str,
    schema_name: str = "public",
    pipeline_name: Optional[str] = None,
    include_profiling: bool = True,
    include_lineage: bool = True,
    docker_mode: bool = False,
) -> Dict:
    """Generate DataHub ingestion configuration for a PostgreSQL database.

    Args:
        database_name: PostgreSQL database name to ingest
        schema_name: Schema name within the database (default: 'public')
        pipeline_name: Optional custom pipeline name
        include_profiling: Enable table/column profiling
        include_lineage: Enable view lineage detection
        docker_mode: If True, use Docker container names instead of localhost

    Returns:
        Dictionary with ingestion configuration
    """
    pg_config = get_postgres_config(database_name)

    if not pipeline_name:
        pipeline_name = f"pg_local_{database_name}"

    # Determine host based on mode
    if docker_mode:
        # Use Docker container name (for ingestion running inside DataHub)
        pg_host = "postgres_db"  # The container_name from docker-compose
        datahub_server = "http://datahub-gms:8080"  # Internal DataHub service name
    else:
        # Use localhost (for direct host-to-host connections, rarely used)
        pg_host = pg_config['host']
        datahub_server = config.get_datahub_url()

    # Base configuration
    config_dict = {
        "pipeline_name": pipeline_name,
        "source": {
            "type": "postgres",
            "config": {
                "host_port": f"{pg_host}:{pg_config['port']}",
                "database": pg_config["database"],
                "username": pg_config["username"],
                "password": pg_config["password"],
                "include_tables": True,
                "include_views": True,
                "schema_pattern": {
                    "allow": [schema_name],
                },
                "stateful_ingestion": {
                    "enabled": True,
                },
            }
        },
        "sink": {
            "type": "datahub-rest",
            "config": {
                "server": datahub_server,
            }
        }
    }

    # Add token if available
    if config.DATAHUB_TOKEN:
        config_dict["sink"]["config"]["token"] = config.DATAHUB_TOKEN

    # Add profiling configuration
    if include_profiling:
        config_dict["source"]["config"]["profiling"] = {
            "enabled": True,
            "profile_table_level_only": False,
            "turn_off_expensive_profiling_metrics": False,
        }

    # Add view lineage configuration
    if include_lineage:
        config_dict["source"]["config"]["include_view_lineage"] = True
        config_dict["source"]["config"]["include_view_column_lineage"] = True

    return config_dict


@app.command("ingest-run")
def ingest_run_command(
    databases: Optional[List[str]] = typer.Option(
        None,
        "--database",
        "-d",
        help="Database(s) to ingest. Can be specified multiple times. If not specified, ingests all databases."
    ),
    schema: str = typer.Option(
        "public",
        "--schema",
        "-s",
        help="Schema name within each database (default: 'public')"
    ),
    profiling: bool = typer.Option(
        True,
        "--profiling/--no-profiling",
        help="Enable/disable table profiling (statistics, row counts, etc.)"
    ),
    lineage: bool = typer.Option(
        True,
        "--lineage/--no-lineage",
        help="Enable/disable view lineage detection"
    ),
    docker_mode: bool = typer.Option(
        False,
        "--docker-mode/--localhost-mode",
        help="Use Docker container names or localhost (default)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show configuration without executing ingestion"
    ),
):
    """Run database metadata ingestion to DataHub using Python SDK.

    This command uses DataHub's Python SDK to programmatically ingest
    metadata from PostgreSQL databases into DataHub.

    By default, uses localhost since the ingestion pipeline runs locally on
    your host machine (not inside containers).

    Examples:
        # Ingest all databases (uses localhost - default)
        dhub datahub ingest-run

        # Ingest specific databases
        dhub datahub ingest-run -d employees_db -d customer_db

        # Ingest without profiling (faster)
        dhub datahub ingest-run --no-profiling

        # Show config without running
        dhub datahub ingest-run --dry-run

        # Use Docker container names (only if running inside a container)
        dhub datahub ingest-run --docker-mode
    """
    console.print("[bold blue]DataHub Database Ingestion[/bold blue]\n")

    # Determine which databases to ingest
    databases_to_ingest = databases if databases else DATABASE_LIST

    console.print(f"[cyan]Target databases:[/cyan] {', '.join(databases_to_ingest)}")
    console.print(f"[cyan]Schema:[/cyan] {schema}")
    console.print(f"[cyan]Connection mode:[/cyan] {'Docker network' if docker_mode else 'Localhost (host machine)'}")
    console.print(f"[cyan]Profiling:[/cyan] {'enabled' if profiling else 'disabled'}")
    console.print(f"[cyan]View lineage:[/cyan] {'enabled' if lineage else 'disabled'}\n")

    # Verify databases exist
    console.print("[dim]Verifying databases exist...[/dim]")
    try:
        import psycopg
        from psycopg.rows import dict_row

        # Connect to default postgres database to check which databases exist
        conn_string = f"host={config.POSTGRES_HOST} port={config.POSTGRES_PORT} dbname=postgres user={config.POSTGRES_USER} password={config.POSTGRES_PASSWORD}"

        with psycopg.connect(conn_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT datname
                    FROM pg_database
                    WHERE datname = ANY(%s) AND datistemplate = false
                """, (databases_to_ingest,))
                existing_databases = [row["datname"] for row in cur.fetchall()]

        if not existing_databases:
            console.print("[red]Error: None of the specified databases exist[/red]")
            raise typer.Exit(1)

        missing_databases = set(databases_to_ingest) - set(existing_databases)
        if missing_databases:
            console.print(f"[yellow]Warning: Databases not found: {', '.join(missing_databases)}[/yellow]")

        databases_to_ingest = existing_databases
        console.print(f"[green]✓ Found {len(databases_to_ingest)} database(s)[/green]\n")

    except Exception as e:
        console.print(f"[red]Database connection error: {e}[/red]")
        raise typer.Exit(1)

    # Run ingestion for each database
    success_count = 0
    failed_count = 0

    for database in databases_to_ingest:
        console.print(f"[bold]{'─' * 60}[/bold]")
        console.print(f"[bold cyan]Database: {database}[/bold cyan]\n")

        # Generate configuration
        config_dict = generate_ingestion_config(
            database_name=database,
            schema_name=schema,
            include_profiling=profiling,
            include_lineage=lineage,
            docker_mode=docker_mode,
        )

        if dry_run:
            console.print("[dim]Configuration:[/dim]")
            console.print(json.dumps(config_dict, indent=2))
            console.print()
            continue

        try:
            # Import Pipeline here to avoid import errors if not needed
            from datahub.ingestion.run.pipeline import Pipeline

            # Create and run pipeline
            console.print("[dim]Creating ingestion pipeline...[/dim]")
            pipeline = Pipeline.create(config_dict)

            console.print("[dim]Running ingestion (this may take a while)...[/dim]")
            pipeline.run()
            pipeline.raise_from_status()

            console.print(f"[green]✓ Successfully ingested {database}[/green]\n")
            success_count += 1

        except Exception as e:
            console.print(f"[red]✗ Failed to ingest {database}: {e}[/red]\n")
            failed_count += 1

    # Summary
    if not dry_run:
        console.print(f"[bold]{'─' * 60}[/bold]")
        console.print("[bold]Ingestion Summary[/bold]\n")

        table = Table(show_header=False)
        table.add_row("Successful:", f"[green]{success_count}[/green]")
        table.add_row("Failed:", f"[red]{failed_count}[/red]" if failed_count > 0 else "0")
        console.print(table)

        if success_count > 0:
            console.print(f"\n[dim]View metadata: {config.DATAHUB_FRONTEND_URL}[/dim]")


@app.command("ingest-generate-config")
def ingest_generate_config_command(
    databases: Optional[List[str]] = typer.Option(
        None,
        "--database",
        "-d",
        help="Database(s) to generate config for. Can be specified multiple times. If not specified, generates for all databases."
    ),
    schema: str = typer.Option(
        "public",
        "--schema",
        "-s",
        help="Schema name within each database (default: 'public')"
    ),
    output_dir: Path = typer.Option(
        Path("ingest_configs"),
        "--output-dir",
        "-o",
        help="Output directory for generated YAML files"
    ),
    profiling: bool = typer.Option(
        True,
        "--profiling/--no-profiling",
        help="Include profiling in generated config"
    ),
    lineage: bool = typer.Option(
        True,
        "--lineage/--no-lineage",
        help="Include lineage detection in generated config"
    ),
    docker_mode: bool = typer.Option(
        True,
        "--docker-mode/--localhost-mode",
        help="Generate config for Docker network (default) or localhost"
    ),
):
    """Generate DataHub ingestion YAML configuration files.

    Creates YAML configuration files that can be used with the
    'datahub ingest' CLI command for each database.

    By default, generates configs for Docker network (using container names)
    since most ingestion runs inside DataHub infrastructure.

    Examples:
        # Generate configs with Docker network (default)
        dhub datahub ingest-generate-config

        # Generate configs for localhost (rare)
        dhub datahub ingest-generate-config --localhost-mode

        # Generate configs for specific databases
        dhub datahub ingest-generate-config -d employees_db -d customer_db

        # Custom output directory
        dhub datahub ingest-generate-config -o /path/to/configs
    """
    console.print("[bold blue]Generate DataHub Ingestion Configs[/bold blue]\n")

    # Determine which databases to generate configs for
    databases_to_generate = databases if databases else DATABASE_LIST

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[cyan]Output directory:[/cyan] {output_dir}")
    console.print(f"[cyan]Databases:[/cyan] {', '.join(databases_to_generate)}")
    console.print(f"[cyan]Schema:[/cyan] {schema}")
    console.print(f"[cyan]Mode:[/cyan] {'Docker network' if docker_mode else 'Host (localhost)'}\n")

    generated_files = []

    for database in databases_to_generate:
        # Generate configuration
        config_dict = generate_ingestion_config(
            database_name=database,
            schema_name=schema,
            include_profiling=profiling,
            include_lineage=lineage,
            docker_mode=docker_mode,
        )

        # Write to YAML file
        suffix = "_localhost" if not docker_mode else ""
        output_file = output_dir / f"ingest_{database}{suffix}.yml"

        try:
            with open(output_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

            console.print(f"[green]✓[/green] Generated: {output_file}")
            generated_files.append(output_file)

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to generate {output_file}: {e}")

    # Summary
    console.print(f"\n[bold]Generated {len(generated_files)} configuration file(s)[/bold]")

    if generated_files:
        if docker_mode:
            console.print("\n[dim]These configs use Docker container names (postgres_db, datahub-gms)[/dim]")
            console.print("[dim]Use them for DataHub UI-based ingestion or when running inside containers[/dim]")
        else:
            console.print("\n[dim]To run ingestion with these files from your host, use:[/dim]")
            console.print(f"[dim]  datahub ingest -c {generated_files[0]}[/dim]")


@app.command("ingest-list-databases")
def ingest_list_databases_command():
    """List available PostgreSQL databases that can be ingested.

    Shows all databases on the PostgreSQL server along with
    their table counts and whether they're in the default ingestion list.
    """
    console.print("[bold blue]Available PostgreSQL Databases[/bold blue]\n")

    try:
        import psycopg
        from psycopg.rows import dict_row

        # Connect to default postgres database to list all databases
        conn_string = f"host={config.POSTGRES_HOST} port={config.POSTGRES_PORT} dbname=postgres user={config.POSTGRES_USER} password={config.POSTGRES_PASSWORD}"

        with psycopg.connect(conn_string, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Get all databases (excluding templates and system databases)
                cur.execute("""
                    SELECT
                        d.datname AS database_name,
                        pg_catalog.pg_database_size(d.datname) AS size_bytes,
                        pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) AS size
                    FROM pg_catalog.pg_database d
                    WHERE d.datistemplate = false
                        AND d.datname NOT IN ('postgres')
                    ORDER BY d.datname
                """)

                databases = cur.fetchall()

        if not databases:
            console.print("[yellow]No user databases found[/yellow]")
            return

        # Create table
        table = Table(title=f"PostgreSQL Databases ({config.POSTGRES_HOST}:{config.POSTGRES_PORT})")
        table.add_column("Database", style="cyan")
        table.add_column("Size", justify="right", style="magenta")
        table.add_column("Default Ingestion", justify="center")

        for row in databases:
            database_name = row["database_name"]
            size = row["size"]
            in_default = "✓" if database_name in DATABASE_LIST else ""

            table.add_row(
                database_name,
                size,
                f"[green]{in_default}[/green]" if in_default else ""
            )

        console.print(table)
        console.print(f"\n[dim]Total databases: {len(databases)}[/dim]")
        console.print(f"[dim]Default ingestion list: {', '.join(DATABASE_LIST)}[/dim]")

    except Exception as e:
        console.print(f"[red]Database connection error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list-tables")
def list_tables_command(
    database: Optional[str] = typer.Option(
        None,
        "--database",
        "-d",
        help="Filter tables by database name. If not specified, shows tables from all databases."
    ),
    with_columns: bool = typer.Option(
        False,
        "--with-columns",
        help="Include detailed column information (schema, stats, descriptions, relationships)"
    ),
    yaml_format: bool = typer.Option(
        False,
        "--yaml",
        help="Output in YAML format (suppresses all other output)"
    ),
    minified: bool = typer.Option(
        False,
        "--minified",
        help="Use minified YAML format optimized for AI text-to-SQL (removes URNs, row counts, detailed stats). Must be used with --yaml"
    ),
):
    """List all tables from DataHub metadata catalog.

    Queries DataHub's metadata to show all ingested tables/datasets.
    Optionally filter by database name and include column details.

    Examples:
        # List all tables from all databases
        dhub datahub list-tables

        # List tables from a specific database
        dhub datahub list-tables --database employees_db

        # List tables with column details
        dhub datahub list-tables --database employees_db --with-columns

        # Export to YAML format
        dhub datahub list-tables --database employees_db --with-columns --yaml

        # Export minified YAML for AI text-to-SQL (optimized, smaller output)
        dhub datahub list-tables --with-columns --yaml --minified > schema_for_ai.yaml
    """
    # Validate minified flag usage
    if minified and not yaml_format:
        console.print("[red]Error: --minified flag requires --yaml flag[/red]")
        raise typer.Exit(1)

    # When minified is used, columns are always included
    if minified:
        with_columns = True

    if not yaml_format:
        console.print("[bold blue]DataHub Tables Listing[/bold blue]\n")

    try:
        # Connect to DataHub
        gms_url = config.get_datahub_url()
        token = config.DATAHUB_TOKEN if config.DATAHUB_TOKEN else None

        headers = {
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        if not yaml_format:
            console.print(f"[cyan]DataHub URL:[/cyan] {gms_url}")
            if database:
                console.print(f"[cyan]Filtering by database:[/cyan] {database}\n")
            else:
                console.print(f"[cyan]Showing:[/cyan] All databases\n")

        # Use DataHub's search API to find datasets
        search_url = f"{gms_url}/entities?action=search"

        # Always search for all datasets, filter later
        search_body = {
            "input": "*",
            "entity": "dataset",
            "start": 0,
            "count": 10000,  # Max results
        }

        if not yaml_format:
            console.print("[dim]Querying DataHub for datasets...[/dim]")
        response = requests.post(search_url, json=search_body, headers=headers, timeout=30)

        if response.status_code != 200:
            if not yaml_format:
                console.print(f"[red]Error: DataHub API returned status {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
            raise typer.Exit(1)

        data = response.json()
        entities = data.get("value", {}).get("entities", [])

        if not entities:
            if not yaml_format:
                console.print("[yellow]No tables found in DataHub[/yellow]")
                if database:
                    console.print(f"[dim]Hint: Make sure '{database}' has been ingested into DataHub[/dim]")
                else:
                    console.print("[dim]Hint: Run 'dhub datahub ingest-run' to ingest database metadata[/dim]")
            return

        # Parse URNs and extract table information
        # URN format: urn:li:dataset:(urn:li:dataPlatform:postgres,database.schema.table,PROD)
        tables_data = []
        for entity in entities:
            urn = entity.get("entity", "")
            if not urn.startswith("urn:li:dataset:"):
                continue

            # Parse the URN to extract database, schema, and table
            platform, db_name, schema_name, table_name, environment = parse_table_urn(urn)

            # Apply database filter if specified
            if database and db_name != database:
                continue

            tables_data.append({
                "platform": platform,
                "database": db_name,
                "schema": schema_name,
                "table": table_name,
                "environment": environment,
                "urn": urn,
            })

        if not tables_data:
            if not yaml_format:
                console.print(f"[yellow]No tables found for database '{database}'[/yellow]")
            return

        # Sort by database, schema, table
        tables_data.sort(key=lambda x: (x["database"], x["schema"], x["table"]))

        # Fetch column details if requested
        if with_columns:
            if not yaml_format:
                console.print(f"\n[dim]Fetching column details for {len(tables_data)} table(s)...[/dim]")

            from rich.progress import Progress, SpinnerColumn, TextColumn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                disable=yaml_format,  # Disable progress bar in YAML mode
            ) as progress:
                task = progress.add_task("Fetching metadata...", total=len(tables_data))

                for table_info in tables_data:
                    details = fetch_dataset_details(table_info["urn"], headers, gms_url)
                    table_info.update(details)
                    progress.advance(task)

        # Output in YAML format
        if yaml_format:
            print_yaml_output(tables_data, with_columns, minified=minified)
            return

        # Display results in table format (non-YAML mode)
        if not with_columns:
            # Simple table view without columns
            results_table = Table(
                title=f"DataHub Tables{' - ' + database if database else ' - All Databases'}",
                show_header=True,
                header_style="bold cyan"
            )
            results_table.add_column("Platform", style="yellow")
            results_table.add_column("Database", style="magenta")
            results_table.add_column("Schema", style="green")
            results_table.add_column("Table", style="blue")
            results_table.add_column("Environment", style="dim")

            for row in tables_data:
                results_table.add_row(
                    row["platform"],
                    row["database"],
                    row["schema"],
                    row["table"],
                    row["environment"]
                )

            console.print(results_table)
            display_summary(console, tables_data)
        else:
            # Detailed view with columns
            for table_info in tables_data:
                display_table_header(console, table_info)

                # Display columns
                if table_info.get("columns") and len(table_info["columns"]) > 0:
                    display_columns_table(console, table_info["columns"])
                    display_column_statistics(console, table_info["columns"])
                else:
                    console.print(f"\n[dim]No column metadata available for this table[/dim]")

        console.print(f"\n[dim]View in DataHub UI: {config.DATAHUB_FRONTEND_URL}/datasets[/dim]")

    except requests.exceptions.ConnectionError:
        if not yaml_format:
            console.print(f"[red]Error: Could not connect to DataHub at {gms_url}[/red]")
            console.print("[dim]Hint: Make sure DataHub is running with 'docker compose --profile quickstart up -d'[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        if not yaml_format:
            console.print(f"[red]Error querying DataHub: {e}[/red]")
        raise typer.Exit(1)


@app.command("update-column-metadata")
def update_column_metadata_command(
    yaml_file: Path = typer.Argument(
        ...,
        help="Path to YAML file with column metadata updates"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be updated without actually updating"
    ),
):
    """Update column descriptions and structured properties from a YAML file.

    The YAML file should have the following structure:

    \b
    tables:
      - database: loans_db
        schema: public
        table: loans
        columns:
          - name: customer_id
            description: "Customer who received the loan"
            structured_properties:
              fk_target_table: "accounts_db.public.customers"
              fk_target_column: "customer_id"
              fk_cross_database: "true"
              fk_relationship_description: "Links loan to customer account"

    Examples:
        # Update metadata from a YAML file
        dhub datahub update-column-metadata metadata.yaml

        # Preview changes without applying
        dhub datahub update-column-metadata metadata.yaml --dry-run
    """
    console.print("[bold blue]Update Column Metadata from YAML[/bold blue]\n")

    # Check if file exists
    if not yaml_file.exists():
        console.print(f"[red]Error: YAML file not found: {yaml_file}[/red]")
        raise typer.Exit(1)

    # Load YAML file
    try:
        with open(yaml_file, 'r') as f:
            config_data = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error reading YAML file: {e}[/red]")
        raise typer.Exit(1)

    # Validate YAML structure
    if not config_data or "tables" not in config_data:
        console.print("[red]Error: YAML file must have a 'tables' key with table definitions[/red]")
        raise typer.Exit(1)

    tables = config_data["tables"]
    if not isinstance(tables, list):
        console.print("[red]Error: 'tables' must be a list[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]YAML file:[/cyan] {yaml_file}")
    console.print(f"[cyan]Tables to update:[/cyan] {len(tables)}")
    console.print(f"[cyan]Mode:[/cyan] {'Dry run (no changes)' if dry_run else 'Live update'}\n")

    # Connect to DataHub
    try:
        emitter = get_datahub_emitter()
        gms_url = config.get_datahub_url()
        console.print(f"[green]Connected to DataHub: {gms_url}[/green]\n")
    except Exception as e:
        console.print(f"[red]Failed to connect to DataHub: {e}[/red]")
        raise typer.Exit(1)

    from datahub.metadata.schema_classes import (
        EditableSchemaMetadataClass,
        EditableSchemaFieldInfoClass,
        StructuredPropertiesClass,
        StructuredPropertyValueAssignmentClass,
    )
    from datahub.emitter.mcp import MetadataChangeProposalWrapper

    total_updated = 0
    total_failed = 0

    # Process each table
    for table_def in tables:
        database = table_def.get("database")
        schema = table_def.get("schema", "public")
        table = table_def.get("table")
        columns = table_def.get("columns", [])

        if not database or not table:
            console.print(f"[yellow]Warning: Skipping table with missing database or table name[/yellow]")
            continue

        # Construct dataset URN
        dataset_name = f"{database}.{schema}.{table}"
        dataset_urn = f"urn:li:dataset:(urn:li:dataPlatform:postgres,{dataset_name},PROD)"

        console.print(f"[bold cyan]{'─' * 80}[/bold cyan]")
        console.print(f"[bold]{database}.{schema}.{table}[/bold]")
        console.print(f"[dim]URN: {dataset_urn}[/dim]\n")

        if not columns:
            console.print("  [yellow]No columns to update[/yellow]\n")
            continue

        # Process each column
        for col_def in columns:
            col_name = col_def.get("name")
            description = col_def.get("description")
            structured_props = col_def.get("structured_properties", {})

            if not col_name:
                console.print("  [yellow]Warning: Skipping column with no name[/yellow]")
                continue

            console.print(f"  [cyan]{col_name}:[/cyan]")

            try:
                # Show what will be updated
                if description:
                    console.print(f"    [dim]Description:[/dim] {description}")

                if structured_props:
                    console.print(f"    [dim]Structured Properties:[/dim]")
                    for prop_name, prop_value in structured_props.items():
                        console.print(f"      [green]{prop_name}:[/green] {prop_value}")

                if dry_run:
                    console.print(f"    [yellow](dry run - not updating)[/yellow]")
                    total_updated += 1
                    continue

                # Update description if provided
                if description:
                    try:
                        # Create editable schema field info
                        editable_field_info = EditableSchemaFieldInfoClass(
                            fieldPath=col_name,
                            description=description,
                        )

                        # Create editable schema metadata
                        editable_schema_metadata = EditableSchemaMetadataClass(
                            editableSchemaFieldInfo=[editable_field_info]
                        )

                        # Create MCP to update field description
                        mcp = MetadataChangeProposalWrapper(
                            entityType="dataset",
                            changeType=ChangeTypeClass.UPSERT,
                            entityUrn=dataset_urn,
                            aspectName="editableSchemaMetadata",
                            aspect=editable_schema_metadata,
                        )

                        emitter.emit_mcp(mcp)
                        console.print(f"    [green]✓ Description updated[/green]")
                    except Exception as e:
                        console.print(f"    [red]✗ Failed to update description: {e}[/red]")
                        total_failed += 1
                        continue

                # Update structured properties if provided
                if structured_props:
                    try:
                        # Build structured property URNs and values
                        properties = []
                        for prop_name, prop_value in structured_props.items():
                            prop_urn = f"urn:li:structuredProperty:{prop_name}"
                            prop_assignment = StructuredPropertyValueAssignmentClass(
                                propertyUrn=prop_urn,
                                values=[prop_value]
                            )
                            properties.append(prop_assignment)

                        # Create the structured properties aspect
                        structured_properties_aspect = StructuredPropertiesClass(
                            properties=properties
                        )

                        # Create field URN (schemaField URN)
                        field_urn = f"urn:li:schemaField:({dataset_urn},{col_name})"

                        # Create MCP to update structured properties on the field
                        mcp = MetadataChangeProposalWrapper(
                            entityType="schemaField",
                            changeType=ChangeTypeClass.UPSERT,
                            entityUrn=field_urn,
                            aspectName="structuredProperties",
                            aspect=structured_properties_aspect,
                        )

                        emitter.emit_mcp(mcp)
                        console.print(f"    [green]✓ Structured properties updated[/green]")
                    except Exception as e:
                        console.print(f"    [red]✗ Failed to update structured properties: {e}[/red]")
                        total_failed += 1
                        continue

                total_updated += 1

            except Exception as e:
                console.print(f"    [red]✗ Error: {e}[/red]")
                total_failed += 1

        console.print()

    # Summary
    console.print(f"[bold]{'─' * 80}[/bold]")
    console.print("[bold]Update Summary[/bold]\n")

    table = Table(show_header=False)
    table.add_row("Total updated:", f"[green]{total_updated}[/green]")
    table.add_row("Total failed:", f"[red]{total_failed}[/red]" if total_failed > 0 else "0")
    console.print(table)

    if dry_run:
        console.print("\n[yellow]This was a dry run. Use without --dry-run to apply changes.[/yellow]")
    elif total_updated > 0:
        console.print(f"\n[dim]View in DataHub UI: {config.DATAHUB_FRONTEND_URL}/datasets[/dim]")


@app.command("register-structured-properties")
def register_structured_properties_command(
    properties_file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to structured properties YAML file (default: databases/datahub/structured-properties.yaml)"
    ),
):
    """Register structured property definitions in DataHub.

    This command reads a YAML file with structured property definitions and
    creates them in DataHub. These properties can then be assigned to schema fields.

    The YAML file should follow DataHub's structured properties format.

    Examples:
        # Register properties from default file
        dhub datahub register-structured-properties

        # Register from custom file
        dhub datahub register-structured-properties --file my-properties.yaml
    """
    console.print("[bold blue]Register Structured Properties in DataHub[/bold blue]\n")

    # Use default file if not specified
    if not properties_file:
        properties_file = Path("databases/datahub/structured-properties.yaml")

    # Check if file exists
    if not properties_file.exists():
        console.print(f"[red]Error: Properties file not found: {properties_file}[/red]")
        console.print("[dim]Hint: Create a structured properties YAML file with property definitions[/dim]")
        raise typer.Exit(1)

    # Load YAML file
    try:
        with open(properties_file, 'r') as f:
            properties_list = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error reading YAML file: {e}[/red]")
        raise typer.Exit(1)

    if not properties_list or not isinstance(properties_list, list):
        console.print("[red]Error: YAML file must contain a list of property definitions[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Properties file:[/cyan] {properties_file}")
    console.print(f"[cyan]Properties to register:[/cyan] {len(properties_list)}\n")

    # Connect to DataHub
    try:
        emitter = get_datahub_emitter()
        gms_url = config.get_datahub_url()
        console.print(f"[green]Connected to DataHub: {gms_url}[/green]\n")
    except Exception as e:
        console.print(f"[red]Failed to connect to DataHub: {e}[/red]")
        raise typer.Exit(1)

    from datahub.metadata.schema_classes import (
        PropertyCardinalityClass,
        StructuredPropertyDefinitionClass,
        PropertyValueClass,
    )
    from datahub.emitter.mcp import MetadataChangeProposalWrapper

    total_registered = 0
    total_failed = 0

    # Process each property definition
    for prop_def in properties_list:
        prop_id = prop_def.get("id") or prop_def.get("qualified_name")
        display_name = prop_def.get("display_name", prop_id)
        description = prop_def.get("description", "")
        prop_type = prop_def.get("type", "string")
        cardinality = prop_def.get("cardinality", "SINGLE")
        entity_types = prop_def.get("entity_types", [])
        allowed_values = prop_def.get("allowed_values", [])

        if not prop_id:
            console.print(f"[yellow]Warning: Skipping property with no id/qualified_name[/yellow]")
            continue

        console.print(f"[cyan]{prop_id}[/cyan]")
        console.print(f"  [dim]Display Name:[/dim] {display_name}")
        console.print(f"  [dim]Type:[/dim] {prop_type}")
        console.print(f"  [dim]Cardinality:[/dim] {cardinality}")

        try:
            # Map cardinality string to enum
            cardinality_map = {
                "SINGLE": PropertyCardinalityClass.SINGLE,
                "MULTIPLE": PropertyCardinalityClass.MULTIPLE,
            }
            cardinality_enum = cardinality_map.get(cardinality.upper(), PropertyCardinalityClass.SINGLE)

            # Map type string to DataHub type URN
            type_map = {
                "string": "urn:li:dataType:datahub.string",
                "number": "urn:li:dataType:datahub.number",
                "date": "urn:li:dataType:datahub.date",
                "urn": "urn:li:dataType:datahub.urn",
            }
            value_type_urn = type_map.get(prop_type.lower(), "urn:li:dataType:datahub.string")

            # Build allowed values if present
            allowed_value_objs = None
            if allowed_values:
                allowed_value_objs = [
                    PropertyValueClass(
                        value=av.get("value"),
                        description=av.get("description", "")
                    )
                    for av in allowed_values
                ]

            # Create structured property definition
            structured_prop_def = StructuredPropertyDefinitionClass(
                qualifiedName=prop_id,
                displayName=display_name,
                description=description,
                valueType=value_type_urn,
                cardinality=cardinality_enum,
                entityTypes=entity_types,
                allowedValues=allowed_value_objs,
            )

            # Create property URN
            property_urn = f"urn:li:structuredProperty:{prop_id}"

            # Create MCP
            mcp = MetadataChangeProposalWrapper(
                entityType="structuredProperty",
                changeType=ChangeTypeClass.UPSERT,
                entityUrn=property_urn,
                aspectName="propertyDefinition",
                aspect=structured_prop_def,
            )

            emitter.emit_mcp(mcp)

            console.print(f"  [green]✓ Registered[/green]\n")
            total_registered += 1

        except Exception as e:
            console.print(f"  [red]✗ Failed: {e}[/red]\n")
            total_failed += 1

    # Summary
    console.print(f"[bold]{'─' * 80}[/bold]")
    console.print("[bold]Registration Summary[/bold]\n")

    table = Table(show_header=False)
    table.add_row("Total registered:", f"[green]{total_registered}[/green]")
    table.add_row("Total failed:", f"[red]{total_failed}[/red]" if total_failed > 0 else "0")
    console.print(table)

    if total_registered > 0:
        console.print(f"\n[green]✓ Structured properties are now available for use[/green]")
        console.print("[dim]You can now assign these properties to schema fields using update-column-metadata[/dim]")
