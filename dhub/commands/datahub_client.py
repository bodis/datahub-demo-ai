"""DataHub GraphQL client for fetching dataset metadata."""

import requests
from typing import Dict, List

from dhub.commands.datahub_utils import parse_foreign_keys, build_stats_map


def build_dataset_graphql_query() -> str:
    """Build GraphQL query to fetch dataset details including schema, stats, and FKs.

    Returns:
        GraphQL query string
    """
    return """
    query getDataset($urn: String!) {
      dataset(urn: $urn) {
        urn
        properties {
          description
          customProperties {
            key
            value
          }
        }
        schemaMetadata {
          fields {
            fieldPath
            nativeDataType
            nullable
            description
          }
          foreignKeys {
            name
            sourceFields {
              fieldPath
            }
            foreignDataset {
              urn
            }
            foreignFields {
              fieldPath
            }
          }
        }
        datasetProfiles {
          rowCount
          columnCount
          fieldProfiles {
            fieldPath
            uniqueCount
            uniqueProportion
            nullCount
            nullProportion
            min
            max
            mean
            median
            stdev
            sampleValues
          }
        }
        tags {
          tags {
            tag {
              urn
              name
            }
          }
        }
      }
    }
    """


def extract_dataset_properties(dataset: Dict) -> tuple:
    """Extract description and custom properties from dataset.

    Args:
        dataset: Dataset object from GraphQL response

    Returns:
        Tuple of (description, properties_dict)
    """
    description = None
    properties = {}

    if dataset.get("properties"):
        props = dataset["properties"]
        description = props.get("description")
        if props.get("customProperties"):
            properties = {
                prop["key"]: prop["value"]
                for prop in props["customProperties"]
            }

    return description, properties


def extract_schema_metadata(dataset: Dict) -> List[Dict]:
    """Extract column schema and foreign keys from dataset.

    Args:
        dataset: Dataset object from GraphQL response

    Returns:
        List of column dictionaries with schema and FK info
    """
    columns = []

    schema_metadata = dataset.get("schemaMetadata")
    if not schema_metadata or not schema_metadata.get("fields"):
        return columns

    # Parse foreign keys
    fk_map = {}
    if schema_metadata.get("foreignKeys"):
        fk_map = parse_foreign_keys(schema_metadata["foreignKeys"])

    # Build column info
    for field in schema_metadata["fields"]:
        field_path = field.get("fieldPath")
        col_info = {
            "name": field_path,
            "type": field.get("nativeDataType"),
            "nullable": field.get("nullable", True),
            "description": field.get("description"),
            "stats": None,
        }

        # Add foreign key info if this field has one
        if field_path in fk_map:
            col_info["foreign_key"] = fk_map[field_path]

        columns.append(col_info)

    return columns


def extract_dataset_profiles(dataset: Dict, columns: List[Dict]) -> tuple:
    """Extract profiling statistics and merge with columns.

    Args:
        dataset: Dataset object from GraphQL response
        columns: List of column dictionaries to merge stats into

    Returns:
        Tuple of (row_count, column_count) and updates columns in-place
    """
    row_count = None
    column_count = None

    profiles = dataset.get("datasetProfiles")
    if not profiles or len(profiles) == 0:
        return row_count, column_count

    # Get the most recent profile (first one)
    latest_profile = profiles[0]

    # Extract table-level stats
    row_count = latest_profile.get("rowCount")
    column_count = latest_profile.get("columnCount")

    # Extract and merge field-level statistics
    if latest_profile.get("fieldProfiles"):
        stats_map = build_stats_map(latest_profile["fieldProfiles"])

        for col in columns:
            field_path = col["name"]
            if field_path in stats_map:
                # Remove None values
                stats = {k: v for k, v in stats_map[field_path].items() if v is not None}
                if stats:
                    col["stats"] = stats

    return row_count, column_count


def extract_tags(dataset: Dict) -> List[str]:
    """Extract tags from dataset.

    Args:
        dataset: Dataset object from GraphQL response

    Returns:
        List of tag names
    """
    tags = []

    if dataset.get("tags") and dataset["tags"].get("tags"):
        tags = [
            tag["tag"].get("name", tag["tag"]["urn"].split(":")[-1])
            for tag in dataset["tags"]["tags"]
            if tag.get("tag")
        ]

    return tags


def fetch_dataset_details(urn: str, headers: Dict[str, str], gms_url: str) -> Dict:
    """Fetch detailed information about a dataset including columns, stats, and relationships.

    Args:
        urn: Dataset URN
        headers: HTTP headers for authentication
        gms_url: DataHub GMS server URL

    Returns:
        Dictionary with detailed dataset information including columns
    """
    details = {
        "columns": [],
        "description": None,
        "tags": [],
        "glossary_terms": [],
        "upstream_tables": [],
        "downstream_tables": [],
        "properties": {},
        "row_count": None,
        "column_count": None,
    }

    try:
        # Build and execute GraphQL query
        graphql_url = f"{gms_url}/api/graphql"
        query = build_dataset_graphql_query()

        request_body = {
            "query": query,
            "variables": {"urn": urn}
        }

        response = requests.post(graphql_url, json=request_body, headers=headers, timeout=10)

        if response.status_code != 200:
            return details

        data = response.json()

        # Check for GraphQL errors
        if data.get("errors"):
            return details

        dataset = data.get("data", {}).get("dataset")
        if not dataset:
            return details

        # Extract all dataset information using helper functions
        details["description"], details["properties"] = extract_dataset_properties(dataset)
        details["columns"] = extract_schema_metadata(dataset)
        details["row_count"], details["column_count"] = extract_dataset_profiles(dataset, details["columns"])
        details["tags"] = extract_tags(dataset)

    except Exception as e:
        # Return partial details if something fails
        pass

    return details
