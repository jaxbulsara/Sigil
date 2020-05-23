from neogm import Graph, node_base, Property
from neogm.cypher import Query

import pytest
import re


@pytest.fixture
def graph():
    graph = Graph()

    yield graph

    graph.delete_all()


def test_simple_node_creation(graph):
    NodeBase = node_base()

    class Character(NodeBase):
        name = Property()

    with pytest.raises(
        AttributeError, match=r"Character has no attribute 'occupation'\."
    ):
        Character(name="Samwise Gamgee", occupation="Gardener")

    sam = Character(name="Samwise Gamgee")
    frodo = Character(name="Frodo Baggins")

    query = Query(graph)
    query.create(sam, "sam")

    assert re.match(
        r"CREATE \(sam:Character{`name`: 'Samwise Gamgee'}\)",
        query._statement.split("\n")[-2],
    )

    query.create(frodo)

    assert re.match(
        r"CREATE \(_([a-z0-9]{8}):Character{`name`: 'Frodo Baggins'}\)",
        query._statement.split("\n")[-2],
    )

    query.return_()

    assert re.match(
        r"RETURN sam,_([a-z0-9]{8})", query._statement.split("\n")[-2]
    )

    query.return_single()

    record = query.run()

    sam_node = record[0]

    assert type(sam_node) == Character
    assert type(sam_node) == str
    assert sam_node.name == "Samwise Gamgee"
    assert sam_node.id is not None
    assert type(sam_node.id) == int
