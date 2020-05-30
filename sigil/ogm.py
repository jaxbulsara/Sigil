from .meta_functions import (
    PROPERTY_GETTER,
    PROPERTY_SETTER,
    ID_GETTER,
    ID_SETTER,
)

from neo4j import GraphDatabase
from copy import deepcopy
from types import FunctionType
from collections.abc import Iterable


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
    def __init__(self, name=None, default=None, default_args=None):
        def _raise_bad_default_type():
            default_is_callable = callable(self.default)
            if not (default_is_callable):
                raise ValueError(
                    f"default must be a Callable, not {type(self.default).__name__}"
                )

        def _raise_bad_default_args():
            default_args_is_list = type(self.default_args) == list
            default_args_is_tuple = type(self.default_args) == tuple
            default_args_is_dict = type(self.default_args) == dict

            default_args_is_valid = (
                default_args_is_list
                or default_args_is_tuple
                or default_args_is_dict
            )

            if not default_args_is_valid:
                raise ValueError(
                    f"default_args must be a list, tuple, or dict, not {type(self.default_args).__name__}"
                )

        self.name = name
        self.value = None
        self.default = default
        self.default_args = default and default_args or tuple()

        if self.default:
            _raise_bad_default_type()
            _raise_bad_default_args()

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
        def _create_function(function_code, name):
            code = function_code.format(name=name)
            compiled_code = compile(code, "<string>", "exec")
            function = FunctionType(compiled_code.co_consts[0], globals(), name)

            return function

        def _set_as_python_property(
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

        def _setup_attributes():
            def _get_class_attributes():
                attributes = [
                    attribute_name
                    for attribute_name in class_dict.keys()
                    if not attribute_name.startswith("__")
                    and attribute_name != "id"
                ]

                return attributes

            def _setup_property(name):
                def _set_property_name(name):
                    class_dict[name].name = class_dict[name].name or name

                def _set_attribute_private(name):
                    private_name = "_" + name

                    original_property = deepcopy(class_dict[name])
                    class_dict[private_name] = original_property

                _set_property_name(name)
                _set_attribute_private(name)

                property_getter = _create_function(PROPERTY_GETTER, name)
                property_setter = _create_function(PROPERTY_SETTER, name)

                _set_as_python_property(
                    name, property_getter, property_setter,
                )

            def _create_id_attribute():
                class_dict["_id"] = None

                id_getter = _create_function(ID_GETTER, "id")
                id_setter = _create_function(ID_SETTER, "id")
                _set_as_python_property("id", id_getter, id_setter)

            attributes = _get_class_attributes()
            for attribute_name in attributes:
                if type(class_dict[attribute_name]) == Property:
                    _setup_property(attribute_name)

            _create_id_attribute()

        def _create_new_class():
            new_class = super(GraphObjectMeta, cls).__new__(
                cls, classname, bases, class_dict
            )

            return new_class

        def _register_new_class(new_class):
            cls._labels.update({classname: new_class})

        _setup_attributes()
        new_class = _create_new_class()
        _register_new_class(new_class)

        return new_class


class GraphObjectBase(metaclass=GraphObjectMeta):
    def __init__(self, **kwargs):
        def _create_private_name(name):
            return "_" + name

        def _get_attribute(private_name):
            return deepcopy(getattr(self, private_name))

        def _set_id():
            _id = kwargs.pop("id", None)

            if _id is not None:
                setattr(self, "id", _id)

        def _set_properties_from_kwargs(node_properties):
            def _assert_attribute_exists(name):
                if not hasattr(type(self), name):
                    raise AttributeError(
                        f"{type(self).__name__} has no attribute '{name}'."
                    )

            def _set_property_from_kwargs(private_name, attribute):
                attribute.value = kwargs[attribute_name]
                setattr(self, private_name, attribute)

            for attribute_name in kwargs:
                _assert_attribute_exists(attribute_name)

                private_name = _create_private_name(attribute_name)
                attribute = _get_attribute(private_name)

                if type(attribute) == Property:
                    _set_property_from_kwargs(private_name, attribute)
                    node_properties.remove(attribute_name)

        def _set_default_properties(node_properties):
            def _raise_no_default(property_name, property_):
                property_has_default = property_.default
                if not property_has_default:
                    raise AttributeError(
                        f"No default defined for property '{property_name}'"
                    )

            for property_name in node_properties:
                private_name = _create_private_name(property_name)
                property_ = _get_attribute(private_name)

                _raise_no_default(property_name, property_)

                if type(property_.default_args) == dict:
                    print(f"{property_.default_args=}")
                    property_.value = property_.default(
                        **property_.default_args
                    )
                else:
                    property_.value = property_.default(*property_.default_args)

                setattr(self, private_name, property_)

        _set_id()

        node_properties = list(self._properties.keys())
        _set_properties_from_kwargs(node_properties)
        _set_default_properties(node_properties)

    @property
    def _label(self):
        return type(self).__name__

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


class NodeBase(GraphObjectBase):
    def __eq__(self, other):
        node_label_is_equal = type(self) == type(other)
        properties_are_equal = self._properties == other._properties
        ids_are_equal = self.id == other.id

        objects_are_equal = False not in [
            node_label_is_equal,
            properties_are_equal,
            ids_are_equal,
        ]

        return objects_are_equal


class MultiLabel:
    pass


class RelationshipBase(GraphObjectBase):
    pass
