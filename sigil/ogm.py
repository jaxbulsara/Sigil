from neo4j import GraphDatabase
from copy import deepcopy
from types import FunctionType


class Graph(GraphDatabase):
    def __init__(
        self,
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password",
        encrypted=False,
        **config,
    ):
        self.driver = GraphDatabase.driver(
            uri, auth=(user, password), encrypted=False, **config
        )

    def close(self):
        self.driver.close()

    def delete_all(self):
        with self.driver.session() as session:
            session.run("MATCH (_) DETACH DELETE _")


class Property:
    def __init__(self, name=None):
        self._name = name
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def __str__(self):
        return f"{self.value}"


class GraphObjectMeta(type):
    def __new__(cls, classname, bases, class_dict):
        attributes = [
            attribute
            for attribute in class_dict.keys()
            if not attribute.startswith("__")
        ]

        for attribute in attributes:
            cls._set_property_name(attribute, class_dict)

        return super(GraphObjectMeta, cls).__new__(
            cls, classname, bases, class_dict
        )

    @classmethod
    def _set_property_name(cls, name, class_dict):
        if type(class_dict[name]) == Property:
            class_dict[name].name = class_dict[name].name or name


class GraphObject:
    @property
    def _properties(self):
        properties = {
            getattr(self, name).name: getattr(self, name).value
            for name in self.__dir__()
            if not name.startswith("_")
            and type(getattr(self, name)) == Property
        }

        return properties

    @property
    def _cypher_properties(self):
        properties = self._properties
        cypher_properties = "{"

        for name, value in properties.items():
            if value and name != "id":
                cypher_properties += f"`{name}`: {repr(value)}"

        cypher_properties += "}"

        return cypher_properties

    def __str__(self):
        return f"{self.__class__.__name__}{self._cypher_properties}"

    def __repr__(self):
        return f"{self.__class__.__name__}(properties={self._properties})"


class NodeBase(GraphObject, metaclass=GraphObjectMeta):
    def __init__(self, **kwargs):
        cls_ = type(self)
        for key in kwargs:
            no_attribute = not hasattr(cls_, key)
            if no_attribute:
                message = f"{cls_.__name__} has no attribute '{key}'."
                raise AttributeError(message)

            attribute = deepcopy(getattr(self, key))
            attribute.value = kwargs[key]
            setattr(self, key, attribute)
