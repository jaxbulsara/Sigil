from .ogm import NodeBase

import secrets

CREATE = "CREATE"
RETURN = "RETURN"


class Query(object):
    def __init__(self, graph, session=None, transaction=None):
        self._graph = graph

        if transaction:
            self._session = transaction.session
            self._transaction = transaction

        elif session:
            self._session = session
            self._transaction = self._session.begin_transaction()

        else:
            self._session = graph.driver.session()
            self._transaction = self._session.begin_transaction()

        self._statement = ""
        self._names = []
        self._return_type = None

    def create(self, graph_object, name=None):
        if not name:
            name = secrets.token_hex(8)
            self._names.append(name)

        if isinstance(graph_object, NodeBase):
            self._create_node(graph_object, name)

    def _create_node(self, node, name=None):
        node = f"({name}:{node})"
        create_statement = f"{CREATE} {node}"

        self._append(create_statement)

    def return_(self, *names):
        if not names:
            names = self._names

        names_statement = ",".join(names)
        return_statement = f"{RETURN} {names_statement}"

        self._append(return_statement)

    def return_single(self):
        self._return_type == "single"

    def _append(self, statement):
        self._statement += statement + "\n"
