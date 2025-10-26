"""DataHub metadata import commands."""

import csv
import requests
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

        # Create domain properties
        domain_properties = DomainPropertiesClass(
            name=name,
            description=description,
        )

        # If there's a parent domain, set it
        if parent_domain_id:
            # Note: Parent domain relationship is set via the parentDomain field
            # However, DomainPropertiesClass doesn't have a parentDomain field in older versions
            # We'll handle this by ensuring parents are created first (topological sort)
            # The parent relationship can be set via a separate MCP if needed
            pass

        # Create MCP
        mcp = MetadataChangeProposalWrapper(
            entityType="domain",
            changeType=ChangeTypeClass.UPSERT,
            entityUrn=make_domain_urn(domain_id),
            aspectName="domainProperties",
            aspect=domain_properties,
        )

        emitter.emit_mcp(mcp)

        # Set parent domain if exists (using separate aspect)
        if parent_domain_id:
            try:
                # Try to import the parent domain aspect
                from datahub.metadata.schema_classes import ParentDomainsClass

                parent_aspect = ParentDomainsClass(
                    parents=[make_domain_urn(parent_domain_id)]
                )

                parent_mcp = MetadataChangeProposalWrapper(
                    entityType="domain",
                    changeType=ChangeTypeClass.UPSERT,
                    entityUrn=make_domain_urn(domain_id),
                    aspectName="parentDomains",
                    aspect=parent_aspect,
                )

                emitter.emit_mcp(parent_mcp)
            except ImportError:
                # ParentDomainsClass not available, skip parent relationship
                console.print(f"[yellow]Warning: Parent domain relationship not set for {domain_id} (ParentDomainsClass not available)[/yellow]")

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
