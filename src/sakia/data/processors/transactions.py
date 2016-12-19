import attr
import asyncio
import sqlite3
from ..entities import Transaction
from ..entities.transaction import parse_transaction_doc
from .nodes import NodesProcessor
from . import tx_lifecycle
from ..connectors import BmaConnector
from duniterpy.api import bma
from duniterpy.documents import Block
from duniterpy.documents import Transaction as TransactionDoc


@attr.s
class TransactionsProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.SourcesRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector
    _table_states = attr.ib(default=attr.Factory(dict))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.transactions_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo)))

    def transfers(self, currency, pubkey):
        """
        Get all transfers from or to a given pubkey
        :param str currency:
        :param str pubkey:
        :return: the list of Transaction entities
        :rtype: List[sakia.data.entities.Transaction]
        """
        return self._repo.get_transfers(currency, pubkey)

    def _try_transition(self, tx, transition_key, inputs):
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
                if type(input) is not transition_key[1][i]:
                    return False
            for transition in tx_lifecycle.states[transition_key]:
                if transition[0](*inputs):
                    if tx.sha_hash:
                        self._logger.debug("{0} : {1} --> {2}".format(tx.sha_hash[:5], tx.state,
                                                                 transition[2].name))
                    else:
                        self._logger.debug("Unsent transfer : {0} --> {1}".format(tx.state,
                                                                             transition[2].name))

                    # If the transition changes data, apply changes
                    if transition[1]:
                        transition[1](tx, *inputs)
                    tx.state = transition[2] | tx.local
                    return True
        return False

    def find_by_hash(self, sha_hash):
        return self._repo.find_one(sha_hash=sha_hash)

    def awaiting(self, currency):
        return self._repo.get_all(currency=currency, state=Transaction.AWAITING) + \
               self._repo.get_all(currency=currency, state=Transaction.AWAITING | Transaction.LOCAL)

    def run_state_transitions(self, tx, *inputs):
        """
        Try all current state transitions with inputs
        :param sakia.data.entities.Transaction tx: the transaction
        :param tuple inputs: The inputs passed to the transitions
        :return: True if the transaction changed state
        :rtype: bool
        """
        transition_keys = [k for k in tx_lifecycle.states.keys() if k[0] | Transaction.LOCAL == tx.state]
        for key in transition_keys:
            if self._try_transition(tx, key, inputs):
                return True
        return False

    def cancel(self, tx):
        """
        Cancel a local transaction
        :param sakia.data.entities.Transaction tx: the transaction
        """
        self.run_state_transitions(tx, ())

    async def send(self, tx, txdoc, community):
        """
        Send a transaction and update the transfer state to AWAITING if accepted.
        If the transaction was refused (return code != 200), state becomes REFUSED
        The txdoc is saved as the transfer txdoc.

        :param sakia.data.entities.Transaction tx: the transaction
        :param txdoc: A transaction duniterpy object
        :param community: The community target of the transaction
        """
        tx.sha_hash = txdoc.sha_hash
        responses = await community.bma_access.broadcast(bma.tx.process,
                                                         post_args={'transaction': txdoc.signed_raw()})
        blockUID = community.network.current_blockUID
        block = await community.bma_access.future_request(bma.blockchain.block,
                                                          req_args={'number': blockUID.number})
        signed_raw = "{0}{1}\n".format(block['raw'], block['signature'])
        block_doc = Block.from_signed_raw(signed_raw)
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.text()
        self.run_state_transitions(tx, ([r.status for r in responses], block_doc))
        self.run_state_transitions(tx, ([r.status for r in responses],))
        return result

    async def initialize_transactions(self, identity, log_stream):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param sakia.data.entities.Identity pubkey:
        :param function log_stream:
        """
        history_data = await self._bma_connector.get(identity.currency, bma.tx.history,
                                                     req_args={'pubkey': identity.pubkey})
        txid = 0
        nb_tx = len(history_data["history"]["sent"]) + len(history_data["history"]["received"])
        log_stream("Found {0} transactions".format(nb_tx))
        for sent_data in history_data["history"]["sent"] + history_data["history"]["received"]:
            sent = TransactionDoc.from_bma_history(history_data["currency"], sent_data)
            log_stream("{0}/{1} transactions".format(txid, nb_tx))
            try:
                self._repo.insert(parse_transaction_doc(sent, identity.pubkey, sent_data["block_number"],
                                                        sent_data["time"], txid))
            except sqlite3.IntegrityError:
                log_stream("Transaction already registered in database")
            await asyncio.sleep(0)
            txid += 1
