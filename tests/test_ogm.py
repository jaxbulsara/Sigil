from neogm import Graph, NodeBase, Property
from neogm.cypher import Query

import pytest


@pytest.fixture
def graph():
    graph = Graph()

    yield graph

    graph.delete_all()


def test_object_property_assignment(graph):
    class Character(NodeBase):
        name = Property()
        extra_attribute = None

    with pytest.raises(
        AttributeError, match=r"Character class has no attribute 'occupation'\."
    ):
        Character(name="Samwise Gamgee", occupation="Gardener")

    with pytest.raises(
        AttributeError,
        match=r"Character node has no Property 'extra_attribute'\.",
    ):
        Character(name="Samwise Gamgee", extra_attribute="extra")


def test_simple_node_creation(graph):
    class Character(NodeBase):
        name = Property()

    sam = Character(name="Samwise Gamgee")

    query = Query(graph)
    query.create(sam, "sam")
    query.return_("sam")
    query.return_single()

    record = query.run()

    sam_node = record[0]

    assert type(sam_node) == Character
    assert type(sam_node) == str
    assert sam_node.name == "Samwise Gamgee"
    assert sam_node.id is not None
    assert type(sam_node.id) == int
