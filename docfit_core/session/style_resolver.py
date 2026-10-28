"""Property-level cascading with explicit values and inspectable provenance."""
from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class StyleDefinition:
    properties: Mapping
    parent: str | None = None


@dataclass(frozen=True)
class ResolvedStyle:
    properties: dict
    sources: dict


class StyleResolver:
    """Flat property keys are atomic (use e.g. border.top.color).

    None, False and zero are explicit overrides, never treated as missing.
    Role mappings apply in supplied order (e.g. banding, header, total).
    Named style ancestors apply root first, child last; cycles are rejected.
    """

    def __init__(self, app_defaults=None, styles=None):
        self.app_defaults = deepcopy(app_defaults or {})
        self.styles = deepcopy(styles or {})

    def resolve(self, *, agency_profile=None, document_theme=None,
                parent_style=None, table_role_conditions=(),
                direct_formatting=None):
        values, sources = {}, {}

        def layer(properties, name):
            for key, value in properties.items():
                values[key] = deepcopy(value)
                sources[key] = name

        layer(self.app_defaults, "app_defaults")
        layer(agency_profile or {}, "agency_profile")
        layer(document_theme or {}, "document_theme")
        chain, visited = [], set()
        name = parent_style
        while name is not None:
            if name in visited:
                raise ValueError(f"style inheritance cycle: {name}")
            visited.add(name)
            definition = self.styles[name]  # Unknown styles fail closed.
            chain.append((name, definition))
            name = definition.parent
        for name, definition in reversed(chain):
            layer(definition.properties, f"parent_style:{name}")
        for index, properties in enumerate(table_role_conditions):
            layer(properties, f"table_role_conditions:{index}")
        layer(direct_formatting or {}, "direct_formatting")
        return ResolvedStyle(values, sources)
