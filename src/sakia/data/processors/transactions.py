import logging
import attr
import asyncio
import sqlite3
from ..entities import Transaction
from ..entities.transaction import parse_transaction_doc
from .nodes import NodesProcessor
from . import tx_lifecycle
from ..connectors import BmaConnector, parse_bma_responses
from duniterpy.api import bma
from duniterpy.documents import Transaction as TransactionDoc


@attr.s
class TransactionsProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.SourcesRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector
    _table_states = attr.ib(default=attr.Factory(dict))
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.transactions_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo), app.parameters))

    def next_txid(self, currency, block_number):
        """
        :param str currency:
        :param str block_number:
        :rtype: int
        """
        transfers = self._repo.get_all(currency=currency, written_on=block_number)
        return max([tx.txid for tx in transfers]) if transfers else 0

    def transfers(self, currency, pubkey):
        """
        Get all transfers from or to a given pubkey
        :param str currency:
        :param str pubkey:
        :return: the list of Transaction entities
        :rtype: List[sakia.data.entities.Transaction]
        """
        return self._repo.get_transfers(currency, pubkey)

    def _try_transition(self, tx, transition_key, *inputs):
        """
        Try the transition defined by the given transition_key
        with inputs
        :param sakia.data.entities.Transaction tx: the transaction
        :param tuple transition_key: The transition key in the table states
        :param tuple inputs: The inputs
        :return: True if the transition was applied
        :rtype: bool
        """
        if len(inputs) == len(transition_key[1]):
            for i, input in enumerate(inputs):
                if not isinstance(input, transition_key[1][i]):
                    return False
            for transition in tx_lifecycle.states[transition_key]:
                if transition[0](tx, *inputs):
                    if tx.sha_hash:
                        self._logger.debug("{0} : {1} --> {2}".format(tx.sha_hash[:5], tx.state,
                                                                      transition[2]))
                    else:
                        self._logger.debug("Unsent transfer : {0} --> {1}".format(tx.state,
                                                                                  transition[2]))

                    # If the transition changes data, apply changes
                    if transition[1]:
                        transition[1](tx, *inputs)
                    tx.state = transition[2]
                    return True
        return False

    def commit(self, tx):
        try:
            self._repo.insert(tx)
        except sqlite3.IntegrityError:
            self._repo.update(tx)

    def find_by_hash(self, sha_hash):
        return self._repo.get_one(sha_hash=sha_hash)

    def awaiting(self, currency):
        return self._repo.get_all(currency=currency, state=Transaction.AWAITING)

    def run_state_transitions(self, tx, *inputs):
        """
        Try all current state transitions with inputs
        :param sakia.data.entities.Transaction tx: the transaction
        :param tuple inputs: The inputs passed to the transitions
        :return: True if the transaction changed state
        :rtype: bool
        """
        transition_keys = [k for k in tx_lifecycle.states.keys() if k[0] == tx.state]
        for key in transition_keys:
            if self._try_transition(tx, key, *inputs):
                self._repo.update(tx)
                return True
        return False

    def cancel(self, tx):
        """
        Cancel a local transaction
        :param sakia.data.entities.Transaction tx: the transaction
        """
        self.run_state_transitions(tx, ())

    async def send(self, tx, txdoc, currency):
        """
        Send a transaction and update the transfer state to AWAITING if accepted.
        If the transaction was refused (return code != 200), state becomes REFUSED
        The txdoc is saved as the transfer txdoc.

        :param sakia.data.entities.Transaction tx: the transaction
        :param txdoc: A transaction duniterpy object
        :param currency: The community target of the transaction
        """
        self._logger.debug(txdoc.signed_raw())
        self._repo.insert(tx)
        responses = await self._bma_connector.broadcast(currency, bma.tx.process, req_args={'transaction': txdoc.signed_raw()})
        result = await parse_bma_responses(responses)
        self.run_state_transitions(tx, [r.status for r in responses if not isinstance(r, BaseException)])
        return result, tx

    async def initialize_transactions(self, connection, log_stream):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param sakia.data.entities.Connection connection:
        :param function log_stream:
        """
        history_data = await self._bma_connector.get(connection.currency, bma.tx.history,
                                                     req_args={'pubkey': connection.pubkey}, verify=False)
        txid = 0
        nb_tx = len(history_data["history"]["sent"]) + len(history_data["history"]["received"])
        log_stream("Found {0} transactions".format(nb_tx))
        transactions = []
        for sent_data in history_data["history"]["sent"] + history_data["history"]["received"]:
            sent = TransactionDoc.from_bma_history(history_data["currency"], sent_data)
            log_stream("{0}/{1} transactions".format(txid, nb_tx))
            try:
                tx = parse_transaction_doc(sent, connection.pubkey, sent_data["block_number"],
                                           sent_data["time"], txid)
                self._repo.insert(tx)
                transactions.append(tx)
            except sqlite3.IntegrityError:
                log_stream("Transaction already registered in database")
            await asyncio.sleep(0)
            txid += 1
        return transactions

    def cleanup_connection(self, connection, connections_pubkeys):
        """
        Cleanup connections data after removal
        :param sakia.data.entities.Connection connection: removed connection
        :param List[str] connections_pubkeys: pubkeys of existing connections
        :return:
        """
        sent = self._repo.get_all(currency=connection.currency, issuer=connection.pubkey)
        for tx in sent:
            if tx.receiver not in connections_pubkeys:
                self._repo.drop(tx)
        received = self._repo.get_all(currency=connection.currency, receiver=connection.pubkey)
        for tx in received:
            if tx.issuer not in connections_pubkeys:
                self._repo.drop(tx)
