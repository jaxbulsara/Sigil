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
    pass


class GraphObjectMeta(type):
    def __init__(cls, classname, bases, dict_):
        type.__init__(cls, classname, bases, dict_)


class GraphObject:
    @property
    def cypher_properties(self):
        properties = vars(self)
        cypher_properties = "{"

        for name, value in properties.items():
            if value:
                cypher_properties += f"`{name}`: {repr(value)}"

        cypher_properties += "}"

        return cypher_properties


def _constructor(self, **kwargs):
    cls_ = type(self)
    for key in kwargs:
        no_attribute = not hasattr(cls_, key)
        if no_attribute:
            message = f"{cls_.__name__} has no attribute '{key}'."
            raise AttributeError(message)

        setattr(self, key, kwargs[key])


_constructor.__name__ = "__init__"


def _node_cypher_repr(self):
    return f"{self.__class__.__name__}{self.cypher_properties}"


_node_cypher_repr.__name__ = "__repr__"


def node_base(
    cls=GraphObject,
    name="NodeBase",
    constructor=_constructor,
    representer=_node_cypher_repr,
    metaclass=GraphObjectMeta,
):
    bases = not isinstance(cls, tuple) and (cls,) or cls
    class_dict = dict()

    if constructor:
        class_dict["__init__"] = constructor

    if representer:
        class_dict["__repr__"] = representer

    return metaclass(name, bases, class_dict)
