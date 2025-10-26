"""Utility functions for parsing DataHub data."""

from typing import Dict, List


def parse_dataset_urn(urn: str) -> str:
    """Parse a dataset URN to extract the table name.

    Args:
        urn: DataHub dataset URN

    Returns:
        Table name in format database.schema.table, or original URN if parsing fails
    """
    try:
        parts = urn.split("(", 1)[1].rsplit(")", 1)[0]
        components = parts.split(",")
        if len(components) >= 2:
            return components[1]  # database.schema.table
        return urn
    except Exception:
        return urn


def parse_foreign_keys(foreign_keys: List[Dict]) -> Dict[str, Dict]:
    """Parse foreign key definitions into a field-to-FK mapping.

    Args:
        foreign_keys: List of foreign key definitions from GraphQL

    Returns:
        Dictionary mapping field paths to FK info
    """
    fk_map = {}

    for fk in foreign_keys:
        source_fields = fk.get("sourceFields", [])
        foreign_dataset_urn = fk.get("foreignDataset", {}).get("urn")
        foreign_fields = fk.get("foreignFields", [])

        if source_fields and foreign_dataset_urn and foreign_fields:
            for source_field in source_fields:
                field_path = source_field.get("fieldPath")
                if field_path:
                    foreign_table = parse_dataset_urn(foreign_dataset_urn)
                    foreign_field = foreign_fields[0].get("fieldPath") if foreign_fields else None

                    fk_map[field_path] = {
                        "foreign_table": foreign_table,
                        "foreign_column": foreign_field,
                        "constraint_name": fk.get("name"),
                    }

    return fk_map


def build_stats_map(field_profiles: List[Dict], max_samples: int = 4) -> Dict[str, Dict]:
    """Build a mapping of field names to their statistics.

    Args:
        field_profiles: List of field profile data from GraphQL
        max_samples: Maximum number of sample values to include

    Returns:
        Dictionary mapping field paths to stats
    """
    stats_map = {}

    for fp in field_profiles:
        field_path = fp.get("fieldPath")
        if not field_path:
            continue

        # Limit sample values
        sample_values = fp.get("sampleValues", [])
        if len(sample_values) > max_samples:
            sample_values = sample_values[:max_samples]

        stats_map[field_path] = {
            "unique_count": fp.get("uniqueCount"),
            "unique_proportion": fp.get("uniqueProportion"),
            "null_count": fp.get("nullCount"),
            "null_proportion": fp.get("nullProportion"),
            "min": fp.get("min"),
            "max": fp.get("max"),
            "mean": fp.get("mean"),
            "median": fp.get("median"),
            "stdev": fp.get("stdev"),
            "sample_values": sample_values,
        }

    return stats_map


def parse_table_urn(urn: str) -> tuple:
    """Parse a table URN to extract database, schema, and table name.

    Args:
        urn: DataHub dataset URN

    Returns:
        Tuple of (platform, database, schema, table, environment)
    """
    try:
        # URN format: urn:li:dataset:(urn:li:dataPlatform:postgres,database.schema.table,PROD)
        parts = urn.split("(", 1)[1].rsplit(")", 1)[0]
        components = parts.split(",")

        if len(components) >= 2:
            platform = components[0].split(":")[-1]  # Extract platform (e.g., "postgres")
            full_table_name = components[1]  # e.g., "employees_db.public.departments"
            environment = components[2] if len(components) > 2 else "PROD"

            # Split database.schema.table
            name_parts = full_table_name.split(".")
            if len(name_parts) == 3:
                db_name, schema_name, table_name = name_parts
            elif len(name_parts) == 2:
                db_name = "unknown"
                schema_name, table_name = name_parts
            else:
                db_name = "unknown"
                schema_name = "public"
                table_name = full_table_name

            return platform, db_name, schema_name, table_name, environment

    except Exception:
        pass

    return "unknown", "unknown", "public", urn, "PROD"
