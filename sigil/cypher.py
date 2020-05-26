from .ogm import NodeBase

from neo4j import BoltStatementResult, Record
from neo4j.types import Node
from logging import getLogger, StreamHandler, DEBUG

import neobolt
import secrets

CREATE = "CREATE"
RETURN = "RETURN"

class SigilStatementResult(BoltStatementResult):
    def __init__(self, result):
        self._session = result._session
        self._hydrant = result._hydrant
        self._metadata = result._metadata
        self._records = result._records
        self._summary = result._summary

    def records(self):
        records = self._records
        next_record = records.popleft
        while records:
            next_ = next_record()
            yield self.cast(next_)
        attached = self.attached
        if attached():
            self._session.send()
        while attached():
            self._session.fetch()
            while records:
                next_ = next_record()
                yield self.cast(next_)

    def cast(self, record):
        casted_record = {}
        for key, value in record.items():
            if type(value) == Node:
                for label in value.labels:
                    if label in NodeBase._labels.keys():
                        node_class = NodeBase._labels[label]
                        properties = {dict_item[0]: dict_item[1] for dict_item in value.items()}
                        properties.update({"id": value.id})
                        casted_record.update({key: node_class(**properties)})
                

        return Record(casted_record)


class Query(object):
    def __init__(self, graph, session=None, transaction=None):
        self._graph = graph
        self._statement = ""
        self._names = []
        self._result = None

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

    def run(self, raise_errors=False):
        try:
            result = self._transaction.run(self._statement)
            return SigilStatementResult(result)

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
