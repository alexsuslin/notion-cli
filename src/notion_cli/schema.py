from __future__ import annotations

from typing import Any

from notion_cli.config import DatasourceConfig, default_property_type
from notion_cli.errors import RuntimeCommandError


def check_schema(
    name: str,
    datasource: DatasourceConfig,
    payload: dict[str, Any],
) -> dict[str, object]:
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        raise RuntimeCommandError("schema response must include a properties object")

    issues: list[dict[str, object]] = []
    for field_name, property_name in datasource.properties.items():
        expected = datasource.property_types.get(field_name, default_property_type(field_name))
        actual: str | None = None
        if property_name in properties:
            descriptor = properties[property_name]
            if not isinstance(descriptor, dict) or not isinstance(descriptor.get("type"), str):
                raise RuntimeCommandError(f"schema property '{property_name}' has no valid type")
            actual = descriptor["type"]
        if expected != actual:
            issues.append(
                {
                    "field": field_name,
                    "property": property_name,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {"datasource": name, "valid": not issues, "issues": issues}
