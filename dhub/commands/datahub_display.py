"""Display and formatting functions for DataHub CLI output."""

import yaml
from typing import Dict, List
from rich.console import Console
from rich.table import Table


def format_foreign_key_reference(fk: Dict) -> str:
    """Format a foreign key reference for display.

    Args:
        fk: Foreign key dictionary with table and column info

    Returns:
        Formatted FK reference string
    """
    foreign_table = fk.get("foreign_table", "")
    foreign_col = fk.get("foreign_column", "")

    # Shorten table name if too long
    if len(foreign_table) > 25:
        # Try to show just schema.table
        parts = foreign_table.split(".")
        if len(parts) >= 2:
            foreign_table = f"{parts[-2]}.{parts[-1]}"

    fk_ref = f"→ {foreign_table}.{foreign_col}" if foreign_col else f"→ {foreign_table}"

    if len(fk_ref) > 30:
        fk_ref = fk_ref[:27] + "..."

    return fk_ref


def display_table_header(console: Console, table_info: Dict):
    """Display the table header with name and metadata.

    Args:
        console: Rich console instance
        table_info: Table information dictionary
    """
    console.print(f"\n[bold cyan]{'─' * 80}[/bold cyan]")
    console.print(
        f"[bold magenta]{table_info['database']}[/bold magenta]."
        f"[bold green]{table_info['schema']}[/bold green]."
        f"[bold blue]{table_info['table']}[/bold blue]"
    )

    if table_info.get("description"):
        console.print(f"[dim]Description:[/dim] {table_info['description']}")

    if table_info.get("tags"):
        console.print(f"[dim]Tags:[/dim] {', '.join(table_info['tags'])}")

    if table_info.get("row_count"):
        console.print(f"[dim]Rows:[/dim] {table_info['row_count']:,}")


def display_columns_table(console: Console, columns: List[Dict]):
    """Display columns in a formatted table.

    Args:
        console: Rich console instance
        columns: List of column dictionaries
    """
    console.print(f"\n[bold]Columns ({len(columns)}):[/bold]")

    columns_table = Table(show_header=True, header_style="bold cyan", box=None)
    columns_table.add_column("Name", style="blue", width=25)
    columns_table.add_column("Type", style="yellow", width=18)
    columns_table.add_column("Null", style="dim", width=4)
    columns_table.add_column("FK", style="magenta", width=30)
    columns_table.add_column("Structured Props", style="green", width=15)
    columns_table.add_column("Description", style="white", width=30)

    for col in columns:
        nullable_str = "Yes" if col.get("nullable", True) else "No"
        desc = col.get("description", "") or ""
        if len(desc) > 30:
            desc = desc[:27] + "..."

        # Format foreign key reference
        fk_ref = ""
        if col.get("foreign_key"):
            fk_ref = format_foreign_key_reference(col["foreign_key"])

        # Format structured properties count
        struct_props_str = ""
        if col.get("structured_properties"):
            count = len(col["structured_properties"])
            struct_props_str = f"{count} prop{'s' if count != 1 else ''}"

        columns_table.add_row(
            col["name"] or "",
            col["type"] or "unknown",
            nullable_str,
            fk_ref,
            struct_props_str,
            desc
        )

    console.print(columns_table)

    # Show detailed structured properties for columns that have them
    cols_with_props = [c for c in columns if c.get("structured_properties")]
    if cols_with_props:
        console.print(f"\n[bold]Structured Properties:[/bold]")
        for col in cols_with_props:
            console.print(f"\n  [cyan]{col['name']}:[/cyan]")
            for prop_name, prop_value in col["structured_properties"].items():
                console.print(f"    [dim]{prop_name}:[/dim] {prop_value}")


def display_column_statistics(console: Console, columns: List[Dict]):
    """Display column statistics if available.

    Args:
        console: Rich console instance
        columns: List of column dictionaries with stats
    """
    cols_with_stats = [c for c in columns if c.get("stats")]
    if not cols_with_stats:
        return

    console.print(f"\n[bold]Column Statistics:[/bold]")

    for col in cols_with_stats:
        stats = col["stats"]
        console.print(f"\n  [cyan]{col['name']}:[/cyan]")

        stats_items = []

        # Unique/Distinct stats
        if stats.get("unique_count") is not None:
            unique_count = stats["unique_count"]
            stats_items.append(f"Distinct: {unique_count:,}")

            if stats.get("unique_proportion") is not None:
                unique_pct = stats["unique_proportion"] * 100
                stats_items.append(f"Distinct %: {unique_pct:.1f}%")

        # Null stats
        if stats.get("null_count") is not None:
            null_count = stats["null_count"]
            stats_items.append(f"Nulls: {null_count:,}")

            if stats.get("null_proportion") is not None:
                null_pct = stats["null_proportion"] * 100
                stats_items.append(f"Null %: {null_pct:.1f}%")

        # Numeric stats (handle both numeric and string values)
        if stats.get("min") is not None:
            stats_items.append(f"Min: {stats['min']}")
        if stats.get("max") is not None:
            stats_items.append(f"Max: {stats['max']}")
        if stats.get("mean") is not None:
            mean_val = stats['mean']
            try:
                stats_items.append(f"Mean: {float(mean_val):.2f}")
            except (ValueError, TypeError):
                stats_items.append(f"Mean: {mean_val}")
        if stats.get("median") is not None:
            stats_items.append(f"Median: {stats['median']}")
        if stats.get("stdev") is not None:
            stdev_val = stats['stdev']
            try:
                stats_items.append(f"Stdev: {float(stdev_val):.2f}")
            except (ValueError, TypeError):
                stats_items.append(f"Stdev: {stdev_val}")

        if stats_items:
            console.print(f"    {' | '.join(stats_items)}")

        # Sample values
        if stats.get("sample_values") and len(stats["sample_values"]) > 0:
            samples = stats["sample_values"][:4]  # Show first 4 samples
            console.print(f"    Samples: {', '.join(str(s) for s in samples)}")


def build_minified_yaml_output(tables_data: List[Dict]) -> Dict:
    """Build minified YAML output structure optimized for AI text-to-SQL generation.

    This version removes unnecessary metadata like URNs, row counts, detailed stats,
    and focuses only on schema structure needed for SQL query generation.

    Args:
        tables_data: List of table information dictionaries

    Returns:
        Dictionary ready for YAML serialization (minified for AI)
    """
    output_data = {"databases": {}}

    for table_info in tables_data:
        db_name = table_info["database"]
        schema_name = table_info["schema"]
        table_name = table_info["table"]

        # Initialize database structure if not exists
        if db_name not in output_data["databases"]:
            output_data["databases"][db_name] = {"schemas": {}}

        # Initialize schema structure if not exists
        if schema_name not in output_data["databases"][db_name]["schemas"]:
            output_data["databases"][db_name]["schemas"][schema_name] = {"tables": {}}

        # Build minified table data (only essential fields for SQL generation)
        table_data = {}

        # Only include description if it exists and is meaningful
        if table_info.get("description"):
            table_data["description"] = table_info["description"]

        # Include columns if available
        if table_info.get("columns"):
            table_data["columns"] = []
            for col in table_info["columns"]:
                col_data = {
                    "name": col["name"],
                    "type": col["type"],
                    "nullable": col["nullable"],
                }

                # Include description (critical for AI understanding)
                if col.get("description"):
                    col_data["description"] = col["description"]

                # Include foreign key relationships (essential for joins)
                if col.get("foreign_key"):
                    fk = col["foreign_key"]
                    col_data["foreign_key"] = {
                        "table": fk.get("foreign_table"),
                        "column": fk.get("foreign_column"),
                    }

                # Transform structured properties into cross_db_reference
                # These specialized properties describe cross-database references that behave like FKs
                if col.get("structured_properties"):
                    struct_props = col["structured_properties"]

                    # Check if this has the cross-database FK structured properties
                    has_cross_db_fk = (
                        "fk_target_table" in struct_props or
                        "fk_target_column" in struct_props or
                        "fk_relationship_description" in struct_props
                    )

                    if has_cross_db_fk:
                        # Transform to cross_db_reference format
                        cross_db_ref = {}
                        if "fk_target_table" in struct_props:
                            cross_db_ref["table"] = struct_props["fk_target_table"]
                        if "fk_target_column" in struct_props:
                            cross_db_ref["column"] = struct_props["fk_target_column"]
                        if "fk_relationship_description" in struct_props:
                            cross_db_ref["description"] = struct_props["fk_relationship_description"]

                        if cross_db_ref:
                            col_data["cross_db_reference"] = cross_db_ref
                    else:
                        # Keep other structured properties as-is
                        col_data["structured_properties"] = struct_props

                # Include sample values ONLY for low-cardinality columns (enums/categories)
                # This helps AI understand possible values without bloating the output
                if col.get("stats"):
                    stats = col["stats"]
                    unique_count = stats.get("unique_count")
                    sample_values = stats.get("sample_values", [])

                    # Include samples for categorical/enum columns (low cardinality)
                    if unique_count is not None and unique_count <= 10 and sample_values:
                        col_data["sample_values"] = sample_values[:10]  # Max 10 samples

                table_data["columns"].append(col_data)

        output_data["databases"][db_name]["schemas"][schema_name]["tables"][table_name] = table_data

    return output_data


def build_yaml_output(tables_data: List[Dict], with_columns: bool) -> Dict:
    """Build YAML output structure from table data.

    Args:
        tables_data: List of table information dictionaries
        with_columns: Whether to include column details

    Returns:
        Dictionary ready for YAML serialization
    """
    output_data = {"databases": {}}

    for table_info in tables_data:
        db_name = table_info["database"]
        schema_name = table_info["schema"]
        table_name = table_info["table"]

        # Initialize database structure if not exists
        if db_name not in output_data["databases"]:
            output_data["databases"][db_name] = {"schemas": {}}

        # Initialize schema structure if not exists
        if schema_name not in output_data["databases"][db_name]["schemas"]:
            output_data["databases"][db_name]["schemas"][schema_name] = {"tables": {}}

        # Build table data
        table_data = {
            "platform": table_info["platform"],
            "environment": table_info["environment"],
            "urn": table_info["urn"],
        }

        # Add detailed information if with_columns was specified
        if with_columns:
            if table_info.get("description"):
                table_data["description"] = table_info["description"]
            if table_info.get("tags"):
                table_data["tags"] = table_info["tags"]
            if table_info.get("properties"):
                table_data["properties"] = table_info["properties"]
            if table_info.get("row_count"):
                table_data["row_count"] = table_info["row_count"]
            if table_info.get("column_count"):
                table_data["column_count"] = table_info["column_count"]
            if table_info.get("columns"):
                table_data["columns"] = []
                for col in table_info["columns"]:
                    col_data = {
                        "name": col["name"],
                        "type": col["type"],
                        "nullable": col["nullable"],
                    }
                    if col.get("description"):
                        col_data["description"] = col["description"]
                    if col.get("foreign_key"):
                        col_data["foreign_key"] = col["foreign_key"]
                    if col.get("structured_properties"):
                        col_data["structured_properties"] = col["structured_properties"]
                    if col.get("stats"):
                        # Clean up None values from stats
                        stats = {k: v for k, v in col["stats"].items() if v is not None}
                        if stats:
                            col_data["stats"] = stats

                    table_data["columns"].append(col_data)

        output_data["databases"][db_name]["schemas"][schema_name]["tables"][table_name] = table_data

    return output_data


def print_yaml_output(tables_data: List[Dict], with_columns: bool, minified: bool = False):
    """Print tables data in YAML format.

    Args:
        tables_data: List of table information dictionaries
        with_columns: Whether to include column details
        minified: Whether to use minified format (optimized for AI text-to-SQL)
    """
    if minified:
        output_data = build_minified_yaml_output(tables_data)
    else:
        output_data = build_yaml_output(tables_data, with_columns)
    print(yaml.dump(output_data, default_flow_style=False, sort_keys=False, allow_unicode=True))


def display_summary(console: Console, tables_data: List[Dict]):
    """Display summary statistics by database.

    Args:
        console: Rich console instance
        tables_data: List of table information dictionaries
    """
    db_counts = {}
    for row in tables_data:
        db_counts[row["database"]] = db_counts.get(row["database"], 0) + 1

    console.print(f"\n[bold]Total:[/bold] {len(tables_data)} table(s)")
    if len(db_counts) > 1:
        console.print("\n[bold]By Database:[/bold]")
        for db_name, count in sorted(db_counts.items()):
            console.print(f"  [cyan]{db_name}:[/cyan] {count} table(s)")
