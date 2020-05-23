from .ogm import NodeBase

CREATE = "CREATE"


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

    def create(self, graph_object, name=None):
        print(f"{name}:{graph_object}")
        if isinstance(object, NodeBase):
            self._create_node(graph_object, name)

    def _create_node(self, node, name=None):
        node = f"({name}:{node})"
        create_statement = f"{CREATE} {node}\n"

        self._statement += create_statement

        print(self._statement)
