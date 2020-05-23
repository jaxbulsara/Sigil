from neo4j import GraphDatabase


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
    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class GraphObject:
    @property
    def properties(self):
        object_attributes = dir(self)
        object_attributes.remove("properties")
        object_attributes.remove("cypher_properties")

        object_properties = {
            attribute: getattr(self, attribute).value
            for attribute in object_attributes
            if isinstance(getattr(self, attribute), Property)
        }

        return object_properties

    @property
    def cypher_properties(self):
        properties = self.properties
        cypher_properties = "{"

        for name, value in properties.items():
            if value:
                cypher_properties += f"`{name}`: {repr(value)}"

        cypher_properties += "}"

        return cypher_properties


class NodeBase(GraphObject):
    def __init__(self, **properties):
        def raise_no_attribute():
            no_attribute = not hasattr(self, name)
            if no_attribute:
                message = f"{self.class_name} class has no attribute '{name}'."
                raise AttributeError(message)

        def raise_no_property():
            no_property = type(_property) != Property
            if no_property:
                message = f"{self.class_name} node has no Property '{name}'."
                raise AttributeError(message)

        self.class_name = self.__class__.__name__
        for name, value in properties.items():
            raise_no_attribute()

            _property = getattr(self, name)

            raise_no_property()

            _property.value = value

    def __repr__(self):
        return f"{self.class_name}{self.cypher_properties}"
