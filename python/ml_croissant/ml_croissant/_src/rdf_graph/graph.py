"""RDF graph module."""

from __future__ import annotations

import typing

from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.graph import (
    children_nodes,
    from_rdf_graph,
)
import networkx as nx
import rdflib
from rdflib.extras import external_graph_libs

if typing.TYPE_CHECKING:
    from ml_croissant._src.structure_graph.base_node import Node


def load_rdf_graph(dict_dataset: dict) -> tuple[rdflib.Graph, nx.MultiDiGraph]:
    """Parses RDF graph with NetworkX from a dict."""
    graph = rdflib.Graph()
    graph.parse(
        data=dict_dataset,
        format="json-ld",
    )
    return graph, external_graph_libs.rdflib_to_networkx_multidigraph(graph)


def _find_entry_object(issues: Issues, graph: nx.MultiDiGraph) -> rdflib.term.BNode:
    """Finds the source entry node without any parent."""
    sources = [
        node
        for node, indegree in graph.in_degree(graph.nodes())
        if indegree == 0 and isinstance(node, rdflib.term.BNode)
    ]
    if len(sources) != 1:
        issues.add_error("Trying to define more than one dataset in the file.")
    return sources[0]


def check_rdf_graph(issues: Issues, graph: nx.MultiDiGraph) -> list[Node]:
    """Validates the graph and populates issues with errors/warnings.

    We first build a NetworkX graph where edges are subject->object with the attribute
    `property`.

    Subject/object/property are RDF triples:
        - `subject`is an ID instanciated by RDFLib.
        - `property` (aka predicate) denotes the relationship (e.g.,
        `https://schema.org/description`).
        - `object` is either the value (e.g., the description) or another `subject`.

    Refer to https://www.w3.org/TR/rdf-concepts to learn more.

    Args:
        issues: the issues that will be modified in-place.
        graph: The NetworkX RDF graph to validate.
    """
    # Check RDF properties in nodes
    source = _find_entry_object(issues, graph)
    metadata = from_rdf_graph(issues, graph, source, None)
    nodes = [metadata]
    dataset_name = metadata.name
    with issues.context(dataset_name=dataset_name, distribution_name=""):
        distributions = children_nodes(metadata, constants.SCHEMA_ORG_DISTRIBUTION)
        nodes += distributions
    record_sets = children_nodes(metadata, constants.ML_COMMONS_RECORD_SET)
    nodes += record_sets
    for record_set in record_sets:
        with issues.context(
            dataset_name=dataset_name,
            record_set_name=record_set.name,
            field_name="",
        ):
            fields = children_nodes(record_set, constants.ML_COMMONS_FIELD)
            nodes += fields
            if len(fields) == 0:
                issues.add_error("The node doesn't define any field.")
            for field in fields:
                sub_fields = children_nodes(field, constants.ML_COMMONS_SUB_FIELD)
                nodes += sub_fields
    return nodes
