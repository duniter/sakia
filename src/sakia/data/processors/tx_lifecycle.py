import time
from sakia.data.entities import Transaction
from duniterpy.documents import Block

def _not_found_in_blockchain(tx, rollback, block, mediantime_target, mediantime_blocks):
    """
    Check if the transaction could not be found in the blockchain
    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param duniterpy.documents.Block block: The block to look for the tx
    :param int mediantime_target: The mediantime to mine a block in the community parameters
    :param int mediantime_blocks: The number of block used to derive the mediantime
    :return: True if the transaction could not be found in a given time
    :rtype: bool
    """
    if not rollback:
        for block_tx in block.transactions:
            if block_tx.sha_hash == tx.sha_hash:
                return False
        if block.time > tx.timestamp + mediantime_target * mediantime_blocks:
            return True
    return False


def _found_in_block(tx, rollback, block):
    """
    Check if the transaction can be found in the blockchain
    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param duniterpy.documents.Block block: The block to check for the transaction
    :return: True if the transaction was found
    :rtype: bool
    """
    if not rollback:
        for block_tx in block.transactions:
            if block_tx.sha_hash == tx.sha_hash:
                return True
    return False


def _broadcast_success(tx, ret_codes, block):
    """
    Check if the retcode is 200 after a POST
    :param sakia.data.entities.Transaction tx: the transaction
    :param list ret_codes: The POST return codes of the broadcast
    :param duniterpy.documents.Block block: The current block used for transition.
    :return: True if the post was successful
    :rtype: bool
    """
    return 200 in ret_codes


def _broadcast_failure(tx, ret_codes):
    """
    Check if no retcode is 200 after a POST
    :param sakia.data.entities.Transaction tx: the transaction
    :param list ret_codes: The POST return codes of the broadcast
    :return: True if the post was failed
    :rtype: bool
    """
    return 200 not in ret_codes


def _reached_enough_confrmation(tx, rollback, current_block, fork_window):
    """
    Check if the transfer reached enough confrmation in the blockchain
    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param duniterpy.documents.Block current_block: The current block of the main blockchain
    :param int fork_window: The number of confrmations needed on the network
    :return: True if the transfer reached enough confrmations
    :rtype: bool
    """
    return not rollback and tx.blockstamp.number + fork_window <= current_block.number


def _rollback_and_removed(tx, rollback, block):
    """
    Check if the transfer is not in the block anymore

    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param duniterpy.documents.Block block: The block to check for the transaction
    :return: True if the transfer is not found in the block
    """
    if rollback:
        if not block or block.blockUID != tx.blockstamp:
            return True
        else:
            return tx.sha_hash not in [t.sha_hash for t in block.transactions]
    return False


def _rollback_in_fork_window(tx, rollback, current_block, fork_window):
    """
    Check if the transfer is not in the block anymore

    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param duniterpy.documents.Block current_block: The block to check for the transaction
    :return: True if the transfer is found in the block
    """
    if rollback:
        return tx.blockstamp.number + fork_window > current_block.number
    return False


def _rollback_and_local(tx, rollback, block):
    """
    Check if the transfer is not in the block anymore

    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param duniterpy.documents.Block block: The block to check for the transaction
    :return: True if the transfer is found in the block
    """
    if rollback and tx.local and block.blockUID == tx.blockstamp:
        return tx.sha_hash not in [t.sha_hash for t in block.transactions]
    return False


def _is_locally_created(tx):
    """
    Check if we can send back the transaction if it was locally created

    :param sakia.data.entities.Transaction tx: the transaction
    :return: True if the transaction was locally created
    """
    return tx.local


def _wait(tx, current_block):
    """
    Set the transfer as AWAITING confrmation.

    :param sakia.data.entities.Transaction tx: the transaction
    :param duniterpy.documents.Block current_block: Current block of the main blockchain
    """
    tx.blockstamp = current_block.blockUID
    tx.timestamp = int(time.time())


def _be_validating(tx, block):
    """
    Action when the transfer ins found in a block

    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param duniterpy.documents.Block block: The block checked
    """
    tx.blockstamp = block.blockUID
    tx.timestamp = block.mediantime


def _drop(tx):
    """
    Cancel the transfer locally.
    The transfer state becomes TransferState.DROPPED.
    :param sakia.data.entities.Transaction tx: the transaction
    """
    tx.blockstamp = None


# Dict containing states of a transfer :
# keys are a tuple containg (current_state, transition_parameters)
# values are tuples containing (transition_test, transition_success, new_state)
states = {
            (Transaction.TO_SEND, (list, Block)):
                (
                    (_broadcast_success, lambda tx, l, b: _wait(tx, b), Transaction.AWAITING),
                    (lambda tx, l, b: _broadcast_failure(tx, l), None, Transaction.REFUSED),
                ),
            (Transaction.TO_SEND, ()):
                ((_is_locally_created, _drop, Transaction.DROPPED),),

            (Transaction.AWAITING, (bool, Block)):
                ((_found_in_block, lambda tx, r, b: _be_validating(tx, b), Transaction.VALIDATING),),
            (Transaction.AWAITING, (bool, Block, int, int)):
                ((_not_found_in_blockchain, None, Transaction.REFUSED),),

            (Transaction.VALIDATING, (bool, Block, int)):
                ((_reached_enough_confrmation, None, Transaction.VALIDATED),),
            (Transaction.VALIDATING, (bool, Block)):
                ((_rollback_and_removed, lambda tx, r, b: _drop(tx), Transaction.DROPPED),),

            (Transaction.VALIDATED, (bool, Block, int)):
                ((_rollback_in_fork_window, lambda tx, r, b, i: _be_validating(tx, b), Transaction.VALIDATING),),

            (Transaction.VALIDATED, (bool, Block)):
                (
                    (_rollback_and_removed, lambda tx, r, b: _drop(tx), Transaction.DROPPED),
                    (_rollback_and_local, lambda tx, r, b: _wait(tx, b), Transaction.AWAITING),
                ),

            (Transaction.REFUSED, ()):
                ((_is_locally_created, _drop, Transaction.DROPPED),)
        }
