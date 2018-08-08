import time
from sakia.data.entities import Transaction
from duniterpy.documents import Block


def _found_in_block(tx, sha_hash, block_number):
    """
    Check if the transaction can be found in the blockchain
    :param sakia.data.entities.Transaction tx: the transaction
    :param str sha_hash: The transaction sha_hash found in history
    :param int block_number: The block_number where the tx was found
    :return: True if the transaction was found
    :rtype: bool
    """
    if sha_hash == tx.sha_hash:
        return True


def _broadcast_success(tx, ret_codes):
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


def _is_locally_created(tx):
    """
    Check if we can send back the transaction if it was locally created

    :param sakia.data.entities.Transaction tx: the transaction
    :return: True if the transaction was locally created
    """
    return tx.local


def _be_validated(tx, sha_hash, block_number):
    """
    Action when the transfer ins found in a block

    :param sakia.data.entities.Transaction tx: the transaction
    :param bool rollback: True if we are in a rollback procedure
    :param str sha_hash: The tx sha_hash found in history
    :param int block_number: The block_number where the tx was found
    """
    tx.written_block = block_number


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
            (Transaction.TO_SEND, (list,)):
                (
                    (_broadcast_success, None, Transaction.AWAITING),
                    (lambda tx, l: _broadcast_failure(tx, l), None, Transaction.REFUSED),
                ),
            (Transaction.TO_SEND, ()):
                ((_is_locally_created, _drop, Transaction.DROPPED),),

            (Transaction.AWAITING, (str, int,)):
                ((_found_in_block, _be_validated, Transaction.VALIDATED),),

            (Transaction.REFUSED, ()):
                ((_is_locally_created, _drop, Transaction.DROPPED),)
        }
