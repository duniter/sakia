import attr
from duniterpy.documents import block_uid
from duniterpy.documents import Transaction as TransactionDoc
from duniterpy.documents.transaction import reduce_base
from sakia.helpers import attrs_tuple_of_str
import math


def parse_transaction_doc(tx_doc, pubkey, block_number, mediantime, txid):
    """
    Parse a transaction
    :param duniterpy.documents.Transaction tx_doc: The tx json data
    :param str pubkey: The pubkey of the transaction to parse, to know if its a receiver or issuer
    :param int block_number: The block number where we found the tx
    :param int mediantime: Median time on the network
    :param int txid: The latest txid
    :return: the found transaction
    """
    receivers = [o.conditions.left.pubkey for o in tx_doc.outputs
                 if o.conditions.left.pubkey != tx_doc.issuers[0]]

    in_issuers = len([i for i in tx_doc.issuers
                      if i == pubkey]) > 0

    in_outputs = len([o for o in tx_doc.outputs
                      if o.conditions.left.pubkey == pubkey]) > 0

    if len(receivers) == 0 and in_issuers:
        receivers = [tx_doc.issuers[0]]
        # Transaction to self
        outputs = [o for o in tx_doc.outputs]
        amount = 0
        for o in outputs:
            amount += o.amount * math.pow(10, o.base)
        amount, amount_base = reduce_base(amount, 0)
    elif in_issuers or in_outputs:
        # If the wallet pubkey is in the issuers we sent this transaction
        if in_issuers:
            outputs = [o for o in tx_doc.outputs
                       if o.conditions.left.pubkey != pubkey]
            amount = 0
            for o in outputs:
                amount += o.amount * math.pow(10, o.base)
        # If we are not in the issuers,
        # maybe we are in the recipients of this transaction
        else:
            outputs = [o for o in tx_doc.outputs
                       if o.conditions.left.pubkey == pubkey]
        amount = 0
        for o in outputs:
            amount += o.amount * math.pow(10, o.base)
        amount, amount_base = reduce_base(amount, 0)
    else:
        return None

    transaction = Transaction(currency=tx_doc.currency,
                              pubkey=pubkey,
                              sha_hash=tx_doc.sha_hash,
                              written_block=block_number,
                              blockstamp=tx_doc.blockstamp,
                              timestamp=mediantime,
                              signatures=tx_doc.signatures,
                              issuers=tx_doc.issuers,
                              receivers=receivers,
                              amount=amount,
                              amount_base=amount_base,
                              comment=tx_doc.comment,
                              txid=txid,
                              state=Transaction.VALIDATED,
                              raw=tx_doc.signed_raw())
    return transaction


@attr.s(hash=True)
class Transaction:
    """
    Transaction entity

    :param str currency: the currency of the transaction
    :param str sha_hash: the hash of the transaction
    :param int written_block: the number of the block
    :param duniterpy.documents.BlockUID blockstamp: the blockstamp of the transaction
    :param int timestamp: the timestamp of the transaction
    :param str signature: the signature
    :param str issuer: the pubkey of the issuer
    :param str receiver: the pubkey of the receiver
    :param int amount: the amount
    :param int amount_base: the amount base
    :param str comment: a comment
    :param str txid: the transaction id to sort transctions
    :param int state: the state of the transaction
    """
    TO_SEND = 0
    AWAITING = 1
    VALIDATED = 4
    REFUSED = 8
    DROPPED = 16

    currency      = attr.ib(convert=str, cmp=True, hash=True)
    pubkey        = attr.ib(convert=str, cmp=True, hash=True)
    sha_hash      = attr.ib(convert=str, cmp=True, hash=True)
    written_block = attr.ib(convert=int, cmp=False)
    blockstamp    = attr.ib(convert=block_uid, cmp=False)
    timestamp     = attr.ib(convert=int, cmp=False)
    signatures    = attr.ib(convert=attrs_tuple_of_str, cmp=False)
    issuers       = attr.ib(convert=attrs_tuple_of_str, cmp=False)
    receivers     = attr.ib(convert=attrs_tuple_of_str, cmp=False)
    amount        = attr.ib(convert=int, cmp=False)
    amount_base   = attr.ib(convert=int, cmp=False)
    comment       = attr.ib(convert=str, cmp=False)
    txid          = attr.ib(convert=int, cmp=False)
    state         = attr.ib(convert=int, cmp=False)
    local         = attr.ib(convert=bool, cmp=False, default=False)
    raw           = attr.ib(convert=str, cmp=False, default="")

    def txdoc(self):
        """
        :rtype: duniterpy.documents.Transaction
        """
        return TransactionDoc.from_signed_raw(self.raw)
