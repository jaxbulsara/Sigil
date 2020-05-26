from sigil import Graph
from neo4j.types import Node

import pytest


@pytest.fixture
def graph():
    graph = Graph()

    yield graph

    graph.delete_all()


def test_graph(graph):
    with graph.driver.session() as session:
        transaction = session.begin_transaction()
        statement = """
        CREATE  (_:TestNode{test_property: 'test_value'})
        RETURN  _
        """
        result = transaction.run(statement).value()
        created_node = result[0]

        assert type(created_node) == Node
        assert tuple(created_node.labels) == ("TestNode",)
        assert created_node["test_property"] == "test_value"
