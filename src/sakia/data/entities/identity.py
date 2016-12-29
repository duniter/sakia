import attr
from duniterpy.documents import block_uid, BlockUID, Identity
from duniterpy import PROTOCOL_VERSION


@attr.s()
class Identity:
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    uid = attr.ib(convert=str, default="")
    blockstamp = attr.ib(convert=block_uid, default=BlockUID.empty())
    signature = attr.ib(convert=str, default="", cmp=False, hash=False)
    # Mediantime of the block referenced by blockstamp
    timestamp = attr.ib(convert=int, default=0, cmp=False, hash=False)
    written_on = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
    revoked_on = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
    member = attr.ib(validator=attr.validators.instance_of(bool), default=False, cmp=False, hash=False)
    membership_buid = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
    membership_timestamp = attr.ib(convert=int, default=0, cmp=False, hash=False)
    membership_type = attr.ib(convert=str, default='', validator=lambda s, a, t: t in ('', 'IN', 'OUT'), cmp=False, hash=False)
    membership_written_on = attr.ib(convert=int, default=0, cmp=False, hash=False)

    def document(self):
        """
        Creates a self cert document for a given identity
        :param sakia.data.entities.Identity identity:
        :return: the document
        :rtype: duniterpy.documents.Identity
        """
        return Identity(PROTOCOL_VERSION, self.currency, self.pubkey,
                        self.uid, self.blockstamp, self.signature)
