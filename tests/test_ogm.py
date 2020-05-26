from sigil import Graph, NodeBase, Property, MultiLabel
from sigil.cypher import Query, SigilStatementResult

from datetime import datetime, timezone

import pytest
import re


@pytest.fixture
def graph():
    graph = Graph()

    yield graph

    graph.delete_all()


def test_simple_node_creation(graph):
    class Character(NodeBase):
        id = Property()

    sam = Character()
    assert sam.id == None

    class Character(NodeBase):
        name = Property()

    with pytest.raises(
        AttributeError, match=r"Character has no attribute 'occupation'\."
    ):
        Character(name="Samwise Gamgee", occupation="Gardener")

    sam = Character(name="Samwise Gamgee")
    frodo = Character(name="Frodo Baggins")
    gandalf = Character(name="Gandalf the White", id=0)

    assert sam.id == None
    assert gandalf.id == 0

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

    result = query.run()

    assert type(result) == SigilStatementResult

    sam_node, frodo_node = tuple(result.values()[0])

    assert type(sam_node) == Character
    assert sam_node._label == "Character"
    assert sam_node._properties == {"name": "Samwise Gamgee"}
    assert type(sam_node.name) == str
    assert sam_node.name == "Samwise Gamgee"
    assert sam_node.id is not None
    assert type(sam_node.id) == int
    assert sam_node != sam


def test_complex_node_creation(graph):
    class Employee(NodeBase):
        name = Property()
        email = Property(unique=True)
        favorite_food = Property(optional=True)
        start_date = Property(default=date.now, default_args=timezone.utc)

        manager = ToRelationship("Manager", "REPORTS_TO")

    class Manager(NodeBase):
        department = Property()
        employees = FromRelationship("Employee", "REPORTS_TO")

    with pytest.raises(
        TypeError, r"Employee expected at least 2 arguments, got 1"
    ):
        Employee(name="Jay Bulsara")

    employee_1 = Employee(name="Richter", email="Richter@smashultimate.com")
    employee_2 = Employee(
        name="Link", email="Link@smashultimate.com", favorite_food="Milk"
    )
    employee_3 = Employee(
        name="Marth",
        email="Marth@smashultimate.com",
        start_date=datetime.fromisoformat("2020-05-22T10:23+04:00"),
    )
    manager_1 = Manager(department="Smash")

    assert type(employee_1) == Employee
    assert type(employee_2) == Employee
    assert type(employee_3) == Employee
    assert type(manager_1) == Manager

    assert employee_1.favorite_food == None
    assert employee_2.favorite_food == "Milk"

    assert type(employee_1.start_date) == datetime
    assert type(employee_3.start_date) == datetime

    employee_1 = MultiLabel(employee_1, manager_1)

    assert type(employee_1) == MultiLabel
    assert employee_1._labels == ("Employee", "Manager")
    assert employee_1["Employee"] == employee_1
    assert employee_1["Manager"] == manager_1

    employee_1.remove("Manager")

    with pytest.raises(KeyError):
        employee_1["Manager"]

    employee_1.add(manager_1)

    assert type(employee_1["Manager"]) == Manager

    employee_1["Manager"].employees.add(employee_2, employee_3)

    query = Query(graph)
    query.create(employee_1, employee_2, employee_3)
    query.run()

    query.clear()
    query.match(employee_1, "employee")
    query.return_("employee")
    matched_employee = query.run().value()

    assert type(matched_employee) == MultiLabel
    assert matched_employee._labels == ("Employee", "Manager")
    assert matched_employee["Employee"] == employee_1
    assert matched_employee["Manager"] == manager_1
    assert type(matched_employee.id) == int

    for employee in matched_employee.employees:
        assert employee.id is not None
        assert type(employee) == Employee
        assert employee.manager.first() == matched_employee["Manager"]
