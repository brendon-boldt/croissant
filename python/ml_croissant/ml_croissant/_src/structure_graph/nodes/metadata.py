"""Metadata module."""

import dataclasses

from ml_croissant._src.structure_graph.base_node import Node


@dataclasses.dataclass(frozen=True)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

    citation: str | None = None
    description: str | None = None
    license: str | None = None
    name: str = ""
    url: str = ""

    def __post_init__(self):
        self.assert_has_mandatory_properties("name", "url")
        self.assert_has_optional_properties("citation", "license")
