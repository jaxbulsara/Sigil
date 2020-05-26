from .ogm import NodeBase

import neobolt
import secrets

CREATE = "CREATE"
RETURN = "RETURN"


class Query(object):
    def __init__(self, graph, session=None, transaction=None):
        self._graph = graph
        self._statement = ""
        self._names = []
        self._return_type = None

        self.initialize(session, transaction)

    def initialize(self, session=None, transaction=None):
        def _init_existing_transaction():
            self._session = transaction.session
            self._transaction = transaction
            self._close_session_on_run = False
            self._close_transaction_on_run = False

        def _init_existing_session():
            self._session = session
            self._transaction = self._session.begin_transaction()
            self._close_session_on_run = False
            self._close_transaction_on_run = True

        def _init_new_session():
            self._session = self._graph.driver.session()
            self._transaction = self._session.begin_transaction()
            self._close_session_on_run = True
            self._close_transaction_on_run = True

        if transaction:
            _init_existing_transaction()

        elif session:
            _init_existing_session()

        else:
            _init_new_session()

    def run(self, raise_errors=False):
        try:
            record = self._transaction.run(self._statement).data()

        except neobolt.exceptions.ClientError as client_error:
            self._transaction.success = False
            if raise_errors:
                raise client_error

        else:
            self._transaction.success = True

        finally:
            if self._close_transaction_on_run:
                self._transaction.close()

            if self._close_session_on_run:
                self._session.close()

    def create(self, graph_object, name=None):
        if not name:
            name = self._generate_name()

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

    def _generate_name(self):
        name = "_" + secrets.token_hex(4)
        while name in self._names:
            name = "_" + secrets.token_hex(4)

        return name

    def _append(self, statement):
        self._statement += statement + "\n"
