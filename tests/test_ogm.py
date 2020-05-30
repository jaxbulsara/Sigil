from sigil import Graph, NodeBase, RelationshipBase, Property, MultiLabel
from sigil.cypher import Query, SigilStatementResult

from datetime import datetime, timezone

import pytest
import re


@pytest.fixture
def graph():
    graph = Graph()

    yield graph

    graph.delete_all()


def test_node_class_id_creation(graph):
    class Character(NodeBase):
        pass

    sam = Character()
    assert sam.id == None


def test_node_class_id_overwrite(graph):
    class Character(NodeBase):
        id = Property()

    sam = Character()
    assert sam.id == None


def test_node_object_set_id(graph):
    class Character(NodeBase):
        pass

    sam = Character(id=0)
    assert sam.id == 0


def test_node_object_extra_attribute(graph):
    class Character(NodeBase):
        name = Property()

    with pytest.raises(
        AttributeError, match=r"Character has no attribute 'occupation'"
    ):
        Character(name="Samwise Gamgee", occupation="Gardener")


def test_node_equality(graph):
    class Character(NodeBase):
        name = Property()

    sam = Character(name="Samwise Gamgee")
    sam_other = Character(name="Samwise Gamgee")

    assert sam == sam_other


def test_single_node_creation(graph):
    class Character(NodeBase):
        name = Property()

    sam = Character(name="Samwise Gamgee")

    query = Query(graph)
    query.create(sam, "sam")

    query = Query(graph)
    query.create(sam, "sam")

    assert re.match(
        r"CREATE \(sam:Character{`name`: 'Samwise Gamgee'}\)",
        query._statement.split("\n")[-2],
    )

    query.return_("sam")

    assert re.match(r"RETURN sam", query._statement.split("\n")[-2])

    result = query.run()

    sam_node = result.value()[0]

    assert type(sam_node) == Character
    assert sam_node._label == "Character"
    assert sam_node._properties == {"name": "Samwise Gamgee"}
    assert type(sam_node.name) == str
    assert sam_node.name == "Samwise Gamgee"
    assert sam_node.id is not None
    assert type(sam_node.id) == int
    assert sam_node != sam


def test_multiple_node_creation(graph):
    class Character(NodeBase):
        name = Property()

    sam = Character(name="Samwise Gamgee")
    frodo = Character(name="Frodo Baggins")

    query = Query(graph)
    query.create(sam)
    query.create(frodo)
    query.return_()

    result = query.run()
    sam_node, frodo_node = tuple(result.values()[0])

    assert type(sam_node) == Character
    assert sam_node._label == "Character"
    assert sam_node._properties == {"name": "Samwise Gamgee"}
    assert type(sam_node.name) == str
    assert sam_node.name == "Samwise Gamgee"
    assert sam_node.id is not None
    assert type(sam_node.id) == int
    assert sam_node != sam

    assert type(frodo_node) == Character
    assert frodo_node._label == "Character"
    assert frodo_node._properties == {"name": "Frodo Baggins"}
    assert type(frodo_node.name) == str
    assert frodo_node.name == "Frodo Baggins"
    assert frodo_node.id is not None
    assert type(frodo_node.id) == int
    assert frodo_node != frodo


def test_wrong_property_default(graph):
    def default_value(value):
        return f"default {value}"

    with pytest.raises(
        ValueError, match=r"default must be a Callable, not int"
    ):

        class TestNode(NodeBase):
            test_property = Property(default=1)

    with pytest.raises(
        ValueError,
        match=r"default_args must be a list, tuple, or dict, not str",
    ):

        class TestNode(NodeBase):
            test_property = Property(
                default=default_value, default_args="hello"
            )


def test_property_default(graph):
    def default_value(value):
        return f"default {value}"

    class TestNode(NodeBase):
        tuple_property = Property(
            default=default_value, default_args=("hello",)
        )
        list_property = Property(default=default_value, default_args=["hello"])
        dict_property = Property(
            default=default_value, default_args=dict(value="hello")
        )

    test_node = TestNode()

    assert test_node.tuple_property == "default hello"
    assert test_node.list_property == "default hello"
    assert test_node.dict_property == "default hello"


# def test_complex_node_creation(graph):
#     class Employee(NodeBase):
#         name = Property()
#         email = Property(unique=True)
#         favorite_food = Property(optional=True)
#         start_date = Property(default=datetime.now, default_args=timezone.utc)

#         manager = ToRelationship("Manager", "REPORTS_TO")

#     class Manager(NodeBase):
#         department = Property()
#         employees = FromRelationship("Employee", "REPORTS_TO")

#     with pytest.raises(
#         TypeError, r"Employee expected at least 2 arguments, got 1"
#     ):
#         Employee(name="Jay Bulsara")

#     employee_1 = Employee(name="Richter", email="Richter@smashultimate.com")
#     employee_2 = Employee(
#         name="Link", email="Link@smashultimate.com", favorite_food="Milk"
#     )
#     employee_3 = Employee(
#         name="Marth",
#         email="Marth@smashultimate.com",
#         start_date=datetime.fromisoformat("2020-05-22T10:23+04:00"),
#     )
#     manager_1 = Manager(department="Smash")

#     assert type(employee_1) == Employee
#     assert type(employee_2) == Employee
#     assert type(employee_3) == Employee
#     assert type(manager_1) == Manager

#     assert employee_1.favorite_food == None
#     assert employee_2.favorite_food == "Milk"

#     assert type(employee_1.start_date) == datetime
#     assert type(employee_3.start_date) == datetime

#     employee_1 = MultiLabel(employee_1, manager_1)

#     assert type(employee_1) == MultiLabel
#     assert employee_1._labels == ("Employee", "Manager")
#     assert employee_1["Employee"] == employee_1
#     assert employee_1["Manager"] == manager_1

#     employee_1.remove("Manager")

#     with pytest.raises(KeyError):
#         employee_1["Manager"]

#     employee_1.add(manager_1)

#     assert type(employee_1["Manager"]) == Manager

#     employee_1["Manager"].employees.add(employee_2, employee_3)

#     query = Query(graph)
#     query.create(employee_1, employee_2, employee_3)
#     query.run()

#     query.clear()
#     query.match(employee_1, "employee")
#     query.return_("employee")
#     matched_employee = query.run().value()

#     assert type(matched_employee) == MultiLabel
#     assert matched_employee._labels == ("Employee", "Manager")
#     assert matched_employee["Employee"] == employee_1
#     assert matched_employee["Manager"] == manager_1
#     assert type(matched_employee.id) == int

#     for employee in matched_employee.employees:
#         assert employee.id is not None
#         assert type(employee) == Employee
#         assert employee.manager.first() == matched_employee["Manager"]


# def test_relationships(graph):
#     query = Query(graph)
#     query.create(person_1 - FRIENDS_WITH > person_2)
#     query.create(person_2 - FRIENDS_WITH > person_3)
#     query.create(person_3 - FRIENDS_WITH > person_4)
#     query.create(person_4 - FRIENDS_WITH > person_5)
#     query.create(person_5 - FRIENDS_WITH > person_6)
#     query.create(person_6 - FRIENDS_WITH > person_1)
#     query.create(person_3 - FRIENDS_WITH > person_1)
#     query.return_("person_1")
#     result = query.run()
#     person_1_node = result.value()[0]

#     query.clear()

#     query.match(
#         Path(
#             person_1_node - FRIENDS_WITH * 2 - Person,
#             "person_1",
#             "friends_with",
#             "other",
#         ),
#         "path",
#     )
#     query.return_()
#     result = query.run()
