"""
Created on 31 janv. 2015

@author: inso
"""
import logging
import time
from ucoinpy.api import bma
from ucoinpy.documents import Block, BlockUID
from PyQt5.QtCore import pyqtSignal, QObject
from enum import Enum


class TransferState(Enum):
    """
    TO_SEND means the transaction wasn't sent yet
    AWAITING means the transaction is waiting to reach K blockchain confrmation
    VALIDATED means the transaction was validated locally and is considered present in the blockchain
    REFUSED means the transaction took too long to be registered in the blockchain,
    therefore it is considered as refused
    DROPPED means the transaction was canceled locally. It can still be validated
    in the blockchain if it was sent, if the guy is unlucky ;)
    """
    TO_SEND = 0
    AWAITING = 1
    VALIDATING = 4
    VALIDATED = 2
    REFUSED = 3
    DROPPED = 5


class Transfer(QObject):
    """
    A transfer is the lifecycle of a transaction.
    """
    transfer_broadcasted = pyqtSignal(str)
    broadcast_error = pyqtSignal(int, str)

    def __init__(self, sha_hash, state, blockUID, metadata, locally_created):
        """
        The constructor of a transfer.
        Check for metadata keys which must be present :
        - receiver
        - block
        - time
        - issuer
        - amount
        - comment

        :param str sha_hash: The hash of the transaction
        :param TransferState state: The state of the Transfer
        :param ucoinpy.documents.BlockUID blockUID: The blockUID of the transaction in the blockchain
        :param dict metadata: The transfer metadata
        """
        assert('receiver' in metadata)
        assert('time' in metadata)
        assert('issuer' in metadata)
        assert('amount' in metadata)
        assert('comment' in metadata)
        assert('issuer_uid' in metadata)
        assert('receiver_uid' in metadata)
        assert('txid' in metadata)
        super().__init__()

        self.sha_hash = sha_hash
        self.state = state
        self.blockUID = blockUID
        self._locally_created = locally_created
        self._metadata = metadata

        self._table_states = {
            (TransferState.TO_SEND, (list, Block)):
                (
                    (self._broadcast_success, lambda l, b: self._wait(b), TransferState.AWAITING),
                    (lambda l,b: self._broadcast_failure(l), None, TransferState.REFUSED),
                ),
            (TransferState.TO_SEND, ()):
                ((self._is_locally_created, self._drop, TransferState.DROPPED),),

            (TransferState.AWAITING, (bool, Block)):
                ((self._found_in_block, lambda r, b: self._be_validating(b), TransferState.VALIDATING),),
            (TransferState.AWAITING, (bool, Block, int, int)):
                ((self._not_found_in_blockchain, None, TransferState.REFUSED),),

            (TransferState.VALIDATING, (bool, Block, int)):
                ((self._reached_enough_confrmation, None, TransferState.VALIDATED),),
            (TransferState.VALIDATING, (bool, Block)):
                ((self._rollback_and_removed, lambda r, b: self._drop(), TransferState.DROPPED),),

            (TransferState.VALIDATED, (bool, Block, int)):
                ((self._rollback_in_fork_window, lambda r, b, i: self._be_validating(b), TransferState.VALIDATING),),

            (TransferState.VALIDATED, (bool, Block)):
                (
                    (self._rollback_and_removed, lambda r, b: self._drop(), TransferState.DROPPED),
                    (self._rollback_and_local, lambda r, b: self._wait(b), TransferState.AWAITING),
                ),

            (TransferState.REFUSED, ()):
                ((self._is_locally_created, self._drop, TransferState.DROPPED),)
        }

    @classmethod
    def initiate(cls, metadata):
        """
        Create a new transfer in a "TO_SEND" state.
        :param dict metadata: The computed metadata of the transfer
        :return: A new transfer
        :rtype: Transfer
        """
        return cls(None, TransferState.TO_SEND, None, metadata, True)

    @classmethod
    def create_from_blockchain(cls, hash, blockUID, metadata):
        """
        Create a new transfer sent from another sakia instance
        :param str hash: The transaction hash
        :param ucoinpy.documents.BlockUID blockUID: The block id were we found the tx
        :param dict metadata: The computed metadata of the transaction
        :return: A new transfer
        :rtype: Transfer
        """
        return cls(hash, TransferState.VALIDATING, blockUID, metadata, False)

    @classmethod
    def load(cls, data):
        """
        Create a new transfer from a dict in json format.
        :param dict data: The loaded data
        :return: A new transfer
        :rtype: Transfer
        """
        return cls(data['hash'],
                   TransferState[data['state']],
                   BlockUID.from_str(data['blockUID']) if data['blockUID'] else None,
                   data['metadata'], data['local'])

    def jsonify(self):
        """
        :return: The transfer as a dict in json format
        """
        return {'hash': self.sha_hash,
                'state': self.state.name,
                'blockUID': str(self.blockUID) if self.blockUID else None,
                'metadata': self._metadata,
                'local': self._locally_created}

    @property
    def metadata(self):
        """
        :return: this transfer metadata
        """
        return self._metadata

    def _not_found_in_blockchain(self, rollback, block, mediantime_target, mediantime_blocks):
        """
        Check if the transaction could not be found in the blockchain
        :param bool rollback: True if we are in a rollback procedure
        :param ucoinpy.documents.Block block: The block to look for the tx
        :param int mediantime_target: The mediantime to mine a block in the community parameters
        :param int mediantime_blocks: The number of block used to derive the mediantime
        :return: True if the transaction could not be found in a given time
        :rtype: bool
        """
        if not rollback:
            for tx in block.transactions:
                if tx.sha_hash == self.sha_hash:
                    return False
            if block.time > self.metadata['time'] + mediantime_target*mediantime_blocks:
                return True
        return False

    def _found_in_block(self, rollback, block):
        """
        Check if the transaction can be found in the blockchain
        :param bool rollback: True if we are in a rollback procedure
        :param ucoinpy.documents.Block block: The block to check for the transaction
        :return: True if the transaction was found
        :rtype: bool
        """
        if not rollback:
            for tx in block.transactions:
                if tx.sha_hash == self.sha_hash:
                    return True
        return False

    def _broadcast_success(self, ret_codes, block):
        """
        Check if the retcode is 200 after a POST
        :param list ret_codes: The POST return codes of the broadcast
        :param ucoinpy.documents.Block block: The current block used for transition.
        :return: True if the post was successful
        :rtype: bool
        """
        return 200 in ret_codes

    def _broadcast_failure(self, ret_codes):
        """
        Check if no retcode is 200 after a POST
        :param list ret_codes: The POST return codes of the broadcast
        :return: True if the post was failed
        :rtype: bool
        """
        return 200 not in ret_codes

    def _reached_enough_confrmation(self, rollback, current_block, fork_window):
        """
        Check if the transfer reached enough confrmation in the blockchain
        :param bool rollback: True if we are in a rollback procedure
        :param ucoinpy.documents.Block current_block: The current block of the main blockchain
        :param int fork_window: The number of confrmations needed on the network
        :return: True if the transfer reached enough confrmations
        :rtype: bool
        """
        return not rollback and self.blockUID.number + fork_window <= current_block.number

    def _rollback_and_removed(self, rollback, block):
        """
        Check if the transfer is not in the block anymore
        :param bool rollback: True if we are in a rollback procedure
        :param ucoinpy.documents.Block block: The block to check for the transaction
        :return: True if the transfer is not found in the block
        """
        if rollback:
            if not block or block.blockUID != self.blockUID:
                return True
            else:
                return self.sha_hash not in [t.sha_hash for t in block.transactions]
        return False

    def _rollback_in_fork_window(self, rollback, current_block, fork_window):
        """
        Check if the transfer is not in the block anymore
        :param bool rollback: True if we are in a rollback procedure
        :param ucoinpy.documents.Block current_block: The block to check for the transaction
        :return: True if the transfer is found in the block
        """
        if rollback:
            return self.blockUID.number + fork_window > current_block.number
        return False

    def _rollback_and_local(self, rollback, block):
        """
        Check if the transfer is not in the block anymore
        :param bool rollback: True if we are in a rollback procedure
        :param ucoinpy.documents.Block block: The block to check for the transaction
        :return: True if the transfer is found in the block
        """
        if rollback and self._locally_created and block.blockUID == self.blockUID:
            return self.sha_hash not in [t.sha_hash for t in block.transactions]
        return False

    def _is_locally_created(self):
        """
        Check if we can send back the transaction if it was locally created
        :return: True if the transaction was locally created
        """
        return self._locally_created

    def _wait(self, current_block):
        """
        Set the transfer as AWAITING confrmation.
        :param ucoinpy.documents.Block current_block: Current block of the main blockchain
        """
        self.blockUID = current_block.blockUID
        self._metadata['time'] = int(time.time())

    def _be_validating(self, block):
        """
        Action when the transfer ins found in a block

        :param bool rollback: True if we are in a rollback procedure
        :param ucoinpy.documents.Block block: The block checked
        """
        self.blockUID = block.blockUID
        self._metadata['time'] = block.mediantime

    def _drop(self):
        """
        Cancel the transfer locally.
        The transfer state becomes TransferState.DROPPED.
        """
        self.blockUID = None

    def _try_transition(self, transition_key, inputs):
        """
        Try the transition defined by the given transition_key
        with inputs
        :param tuple transition_key: The transition key in the table states
        :param tuple inputs: The inputs
        :return: True if the transition was applied
        :rtype: bool
        """
        if len(inputs) == len(transition_key[1]):
            for i, input in enumerate(inputs):
                if type(input) is not transition_key[1][i]:
                    return False
            for transition in self._table_states[transition_key]:
                if transition[0](*inputs):
                    if self.sha_hash:
                        logging.debug("{0} : {1} --> {2}".format(self.sha_hash[:5], self.state.name,
                                                                 transition[2].name))
                    else:
                        logging.debug("Unsent transfer : {0} --> {1}".format(self.state.name,
                                                                 transition[2].name))

                    # If the transition changes data, apply changes
                    if transition[1]:
                        transition[1](*inputs)
                    self.state = transition[2]
                    return True
        return False

    def run_state_transitions(self, inputs):
        """
        Try all current state transitions with inputs
        :param tuple inputs: The inputs passed to the transitions
        :return: True if the transaction changed state
        :rtype: bool
        """
        transition_keys = [k for k in self._table_states.keys() if k[0] == self.state]
        for key in transition_keys:
            if self._try_transition(key, inputs):
                return True
        return False

    def cancel(self):
        """
        Cancel a local transaction
        """
        self.run_state_transitions(())

    async def send(self, txdoc, community):
        """
        Send a transaction and update the transfer state to AWAITING if accepted.
        If the transaction was refused (return code != 200), state becomes REFUSED
        The txdoc is saved as the transfer txdoc.

        :param txdoc: A transaction ucoinpy object
        :param community: The community target of the transaction
        """
        self.sha_hash = txdoc.sha_hash
        responses = await community.bma_access.broadcast(bma.tx.Process,
                post_args={'transaction': txdoc.signed_raw()})
        blockUID = community.network.current_blockUID
        block = await community.bma_access.future_request(bma.blockchain.Block,
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
        self.run_state_transitions(([r.status for r in responses], block_doc))
        self.run_state_transitions(([r.status for r in responses], ))
        return result

    async def get_raw_document(self, community):
        """
        Get the raw documents of this transfer
        """
        block = await community.get_block(self.blockUID.number)
        if block:
            block_doc = Block.from_signed_raw("{0}{1}\n".format(block['raw'], block['signature']))
            for tx in block_doc.transactions:
                if tx.sha_hash == self.sha_hash:
                    return tx
