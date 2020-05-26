from .meta_functions import PROPERTY_GETTER, PROPERTY_SETTER

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
        self.name = name
        self.value = None

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
    _labels = dict()

    def __new__(cls, classname, bases, class_dict):
        def _set_property_name(name):
            class_dict[name].name = class_dict[name].name or name

        def _set_attribute_private(name):
            private_name = "_" + name

            original_property = deepcopy(class_dict[name])
            class_dict[private_name] = original_property

        def _convert_to_python_property(
            name,
            get_function,
            set_function=None,
            del_function=None,
            docstring=None,
        ):
            class_dict[name] = property(
                fget=get_function,
                fset=set_function,
                fdel=del_function,
                doc=docstring,
            )

        def _create_function(function_code, name):
            code = function_code.format(name=name)
            compiled_code = compile(code, "<string>", "exec")
            function = FunctionType(compiled_code.co_consts[0], globals(), name)

            return function

        def _get_class_attributes():
            attributes = [
                attribute_name
                for attribute_name in class_dict.keys()
                if not attribute_name.startswith("__")
            ]

            return attributes

        def _setup_property(name):
            _set_property_name(name)
            _set_attribute_private(name)

            property_getter = _create_function(PROPERTY_GETTER, name)
            property_setter = _create_function(PROPERTY_SETTER, name)

            _convert_to_python_property(
                name, property_getter, property_setter,
            )

        attributes = _get_class_attributes()

        for attribute_name in attributes:
            if type(class_dict[attribute_name]) == Property:
                _setup_property(attribute_name)

        new_class = super(GraphObjectMeta, cls).__new__(
            cls, classname, bases, class_dict
        )

        cls._labels.update({classname: new_class})

        return new_class


class GraphObjectBase:
    @property
    def _properties(self):
        properties = {
            getattr(self, "_" + name).name: getattr(self, name)
            for name in self.__dir__()
            if not name.startswith("_")
            and name != "id"
            and type(getattr(self, "_" + name)) == Property
        }

        return properties

    @property
    def _cypher_properties(self):
        properties = self._properties
        cypher_properties = "{"

        for name, value in properties.items():
            if value:
                cypher_properties += f"`{name}`: {repr(value)}"

        cypher_properties += "}"

        return cypher_properties

    def __str__(self):
        return f"{self.__class__.__name__}{self._cypher_properties}"

    def __repr__(self):
        
        return f"{self.__class__.__name__}(id={getattr(self, 'id', None)}, properties={self._properties})"


class NodeBase(GraphObjectBase, metaclass=GraphObjectMeta):
    def __init__(self, **kwargs):
        def _assert_attribute_exists(name):
            if not hasattr(type(self), name):
                raise AttributeError(
                    f"{type(self).__name__} has no attribute '{name}'."
                )

        def _create_private_name(name):
            return "_" + name

        def _get_attribute(private_name):
            return deepcopy(getattr(self, private_name))

        def _set_property(private_name, attribute):
            attribute.value = kwargs[attribute_name]
            setattr(self, private_name, attribute)

        _id = kwargs.pop("id", None)

        if _id is not None:
            setattr(self, "id", _id)

        for attribute_name in kwargs:
            _assert_attribute_exists(attribute_name)

            private_name = _create_private_name(attribute_name)
            attribute = _get_attribute(private_name)

            if type(attribute) == Property:
                _set_property(private_name, attribute)
