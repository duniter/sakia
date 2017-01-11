import asyncio
import attr
import logging
import jsonschema
from collections import Counter

from duniterpy.key import SigningKey
from duniterpy import PROTOCOL_VERSION
from duniterpy.documents import BlockUID, Block, Certification, Membership, Revocation, InputSource, \
    OutputSource, SIGParameter, Unlock
from duniterpy.documents import Identity as IdentityDoc
from duniterpy.documents import Transaction as TransactionDoc
from duniterpy.documents.transaction import reduce_base
from duniterpy.grammars import output
from duniterpy.api import bma, errors
from sakia.data.entities import Identity, Transaction
from sakia.data.processors import BlockchainProcessor, IdentitiesProcessor, NodesProcessor, \
    TransactionsProcessor, SourcesProcessor
from sakia.data.connectors import BmaConnector
from sakia.errors import NotEnoughChangeError


@attr.s()
class DocumentsService:
    """
    A service to forge and broadcast documents
    to the network

    :param sakia.data.connectors.BmaConnector _bma_connector: the connector
    :param sakia.data.processors.BlockchainProcessor _blockchain_processor: the blockchain processor
    :param sakia.data.processors.IdentitiesProcessor _identities_processor: the identities processor
    :param sakia.data.processors.TransactionsProcessor _transactions_processor: the transactions processor
    :param sakia.data.processors.SourcesProcessor _sources_processor: the sources processor
    """
    _bma_connector = attr.ib()
    _blockchain_processor = attr.ib()
    _identities_processor = attr.ib()
    _transactions_processor = attr.ib()
    _sources_processor = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(BmaConnector(NodesProcessor(app.db.nodes_repo), app.parameters),
                   BlockchainProcessor.instanciate(app),
                   IdentitiesProcessor.instanciate(app),
                   TransactionsProcessor.instanciate(app),
                   SourcesProcessor.instanciate(app))

    async def broadcast_identity(self, connection, password):
        """
        Send our self certification to a target community

        :param sakia.data.entities.Connection connection: the connection published
        :param str password: the private key password
        """
        block_uid = self._blockchain_processor.current_buid(connection.currency)
        timestamp = self._blockchain_processor.time(connection.currency)
        selfcert = IdentityDoc(10,
                               connection.currency,
                               connection.pubkey,
                               connection.uid,
                               block_uid,
                               None)
        key = SigningKey(connection.salt, password, connection.scrypt_params)
        selfcert.sign([key])
        self._logger.debug("Key publish : {0}".format(selfcert.signed_raw()))

        responses = await self._bma_connector.broadcast(connection.currency, bma.wot.add,
                                                        req_args={'identity': selfcert.signed_raw()})
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()

        if result[0]:
            identity = self._identities_processor.get_identity(connection.currency, connection.pubkey, connection.uid)
            if not identity:
                identity = Identity(connection.currency, connection.pubkey, connection.uid)
            identity.blockstamp = block_uid
            identity.signature = selfcert.signatures[0]
            identity.timestamp = timestamp
        else:
            identity = None

        return result, identity

    async def send_membership(self, connection, password, mstype):
        """
        Send a membership document to a target community.
        Signal "document_broadcasted" is emitted at the end.

        :param str currency: the currency target
        :param sakia.data.entities.IdentityDoc identity: the identitiy data
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        :param str mstype: The type of membership demand. "IN" to join, "OUT" to leave
        """
        self._logger.debug("Send membership")

        blockUID = self._blockchain_processor.current_buid(connection.currency)
        membership = Membership(10, connection.currency,
                                connection.pubkey, blockUID, mstype, connection.uid,
                                connection.blockstamp, None)
        key = SigningKey(connection.salt, password, connection.scrypt_params)
        membership.sign([key])
        self._logger.debug("Membership : {0}".format(membership.signed_raw()))
        responses = await self._bma_connector.broadcast(connection.currency, bma.blockchain.membership,
                                                        req_args={'membership': membership.signed_raw()})
        result = (False, "")
        for r in responses:
            if not result[0]:
                if isinstance(r, BaseException):
                    result = (False, str(r))
                else:
                    try:
                        result = (False, (await r.json())["message"])
                    except KeyError:
                        result = (False, await str(r.text()))

            elif r.status == 200:
                result = (True, (await r.json()))
            else:
                await r.release()
        return result

    async def certify(self, connection, password, identity):
        """
        Certify an other identity

        :param sakia.data.entities.Connection connection: the connection published
        :param str password: the private key password
        :param sakia.data.entities.Identity identity: the identity certified
        """
        self._logger.debug("Certdata")
        blockUID = self._blockchain_processor.current_buid(connection.currency)

        certification = Certification(10, connection.currency,
                                      connection.pubkey, identity.pubkey, blockUID, None)

        key = SigningKey(connection.salt, password, connection.scrypt_params)
        certification.sign(identity.document(), [key])
        signed_cert = certification.signed_raw(identity.document())
        self._logger.debug("Certification : {0}".format(signed_cert))

        responses = await self._bma_connector.broadcast(connection.currency, bma.wot.certify, req_args={'cert': signed_cert})
        result = (False, "")
        for r in responses:
            if isinstance(r, BaseException) and not result[0]:
                result = (False, (str(r)))
            else:
                if r.status == 200:
                    result = (True, (await r.json()))
                elif not result[0]:
                    result = (False, (await r.text()))
                else:
                    await r.release()
        return result

    async def revoke(self, currency, identity, salt, password):
        """
        Revoke self-identity on server, not in blockchain

        :param str currency: The currency of the identity
        :param sakia.data.entities.IdentityDoc identity: The certified identity
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        """
        revocation = Revocation(PROTOCOL_VERSION, currency, None)
        self_cert = identity.document()

        key = SigningKey(salt, password)
        revocation.sign(self_cert, [key])

        self._logger.debug("Self-Revokation Document : \n{0}".format(revocation.raw(self_cert)))
        self._logger.debug("Signature : \n{0}".format(revocation.signatures[0]))

        data = {
            'pubkey': identity.pubkey,
            'self_': self_cert.signed_raw(),
            'sig': revocation.signatures[0]
        }
        self._logger.debug("Posted data : {0}".format(data))
        responses = await self._bma_connector.broadcast(currency, bma.wot.Revoke, {}, data)
        result = (False, "")
        for r in responses:
            if r.status == 200:
                result = (True, (await r.json()))
            elif not result[0]:
                result = (False, (await r.text()))
            else:
                await r.release()
        return result

    def generate_revokation(self, connection, password):
        """
        Generate account revokation document for given community

        :param sakia.data.entities.Connection connection: The connection of the identity
        :param str password: The account SigningKey password
        """
        document = Revocation(2, connection.currency, connection.pubkey, "")
        identity = self._identities_processor.get_written(connection.currency, connection.pubkey)
        self_cert = identity[0].document()

        key = SigningKey(connection.salt, password, connection.scrypt_params)

        document.sign(self_cert, [key])
        return document.signed_raw(self_cert)

    def tx_sources(self, amount, amount_base, currency):
        """
        Get inputs to generate a transaction with a given amount of money
        :param int amount: The amount target value
        :param int amount_base: The amount base target value
        :param str currency: The community target of the transaction
        :return: The list of inputs to use in the transaction document
        """

        # such a dirty algorithmm
        # everything should be done again from scratch
        # in future versions

        def current_value(inputs, overhs):
            i = 0
            for s in inputs:
                i += s.amount * (10**s.base)
            for o in overhs:
                i -= o[0] * (10**o[1])
            return i

        amount, amount_base = reduce_base(amount, amount_base)
        available_sources = self._sources_processor.available(currency)
        if available_sources:
            current_base = max([src.base for src in available_sources])
            value = 0
            sources = []
            outputs = []
            overheads = []
            buf_sources = list(available_sources)
            while current_base >= 0:
                for s in [src for src in available_sources if src.base == current_base]:
                    test_sources = sources + [s]
                    val = current_value(test_sources, overheads)
                    # if we have to compute an overhead
                    if current_value(test_sources, overheads) > amount * (10**amount_base):
                        overhead = current_value(test_sources, overheads) - int(amount) * (10**amount_base)
                        # we round the overhead in the current base
                        # exemple : 12 in base 1 -> 1*10^1
                        overhead = int(round(float(overhead) / (10**current_base)))
                        source_value = s.amount * (10**s.base)
                        out = int((source_value - (overhead * (10**current_base)))/(10**current_base))
                        if out * (10**current_base) <= amount * (10**amount_base):
                            sources.append(s)
                            buf_sources.remove(s)
                            overheads.append((overhead, current_base))
                            outputs.append((out, current_base))
                    # else just add the output
                    else:
                        sources.append(s)
                        buf_sources.remove(s)
                        outputs.append((s.amount, s.base))
                    if current_value(sources, overheads) == amount * (10 ** amount_base):
                        return sources, outputs, overheads

                current_base -= 1

        raise NotEnoughChangeError(value, currency, len(sources), amount * pow(10, amount_base))

    def tx_inputs(self, sources):
        """
        Get inputs to generate a transaction with a given amount of money
        :param list[sakia.data.entities.Source] sources: The sources used to send the given amount of money
        :return: The list of inputs to use in the transaction document
        """
        inputs = []
        for s in sources:
            inputs.append(InputSource(s.amount, s.base, s.type, s.identifier, s.noffset))
        return inputs

    def tx_unlocks(self, sources):
        """
        Get unlocks to generate a transaction with a given amount of money
        :param list sources: The sources used to send the given amount of money
        :return: The list of unlocks to use in the transaction document
        """
        unlocks = []
        for i, s in enumerate(sources):
            unlocks.append(Unlock(i, [SIGParameter(0)]))
        return unlocks

    def tx_outputs(self, issuer, receiver, outputs, overheads):
        """
        Get outputs to generate a transaction with a given amount of money
        :param str issuer: The issuer of the transaction
        :param str receiver: The target of the transaction
        :param list outputs: The amount to send
        :param list inputs: The inputs used to send the given amount of money
        :param list overheads: The overheads used to send the given amount of money
        :return: The list of outputs to use in the transaction document
        """
        total = []
        outputs_bases = set(o[1] for o in outputs)
        for base in outputs_bases:
            output_sum = 0
            for o in outputs:
                if o[1] == base:
                    output_sum += o[0]
            total.append(OutputSource(output_sum, base, output.Condition.token(output.SIG.token(receiver))))

        overheads_bases = set(o[1] for o in overheads)
        for base in overheads_bases:
            overheads_sum = 0
            for o in overheads:
                if o[1] == base:
                    overheads_sum += o[0]
            total.append(OutputSource(overheads_sum, base, output.Condition.token(output.SIG.token(issuer))))

        return total

    def prepare_tx(self, issuer, receiver, blockstamp, amount, amount_base, message, currency):
        """
        Prepare a simple Transaction document
        :param str issuer: the issuer of the transaction
        :param str receiver: the target of the transaction
        :param duniterpy.documents.BlockUID blockstamp: the blockstamp
        :param int amount: the amount sent to the receiver
        :param int amount_base: the amount base of the currency
        :param str message: the comment of the tx
        :param str currency: the target community
        :return: the transaction document
        :rtype: duniterpy.documents.Transaction
        """
        result = self.tx_sources(int(amount), amount_base, currency)
        sources = result[0]
        computed_outputs = result[1]
        overheads = result[2]
        self._sources_processor.consume(sources)
        logging.debug("Inputs : {0}".format(sources))

        inputs = self.tx_inputs(sources)
        unlocks = self.tx_unlocks(sources)
        outputs = self.tx_outputs(issuer, receiver, computed_outputs, overheads)
        logging.debug("Outputs : {0}".format(outputs))
        tx = TransactionDoc(10, currency, blockstamp, 0,
                            [issuer], inputs, unlocks,
                            outputs, message, None)
        return tx

    async def send_money(self, connection, password, recipient, amount, amount_base, message):
        """
        Send money to a given recipient in a specified community
        :param sakia.data.entities.Connection connection: The account salt
        :param str password: The account password
        :param str recipient: The pubkey of the recipient
        :param int amount: The amount of money to transfer
        :param int amount_base: The amount base of the transfer
        :param str message: The message to send with the transfer
        """
        blockstamp = self._blockchain_processor.current_buid(connection.currency)
        time = self._blockchain_processor.time(connection.currency)
        key = SigningKey(connection.salt, password, connection.scrypt_params)
        logging.debug("Sender pubkey:{0}".format(key.pubkey))
        try:
            txdoc = self.prepare_tx(connection.pubkey, recipient, blockstamp, amount, amount_base,
                                    message, connection.currency)
            logging.debug("TX : {0}".format(txdoc.raw()))

            txdoc.sign([key])
            logging.debug("Transaction : [{0}]".format(txdoc.signed_raw()))
            txid = self._transactions_processor.next_txid(connection.currency, blockstamp.number)
            tx = Transaction(currency=connection.currency,
                             sha_hash=txdoc.sha_hash,
                             written_block=0,
                             blockstamp=blockstamp,
                             timestamp=time,
                             signature=txdoc.signatures[0],
                             issuer=connection.pubkey,
                             receiver=recipient,
                             amount=amount,
                             amount_base=amount_base,
                             comment=message,
                             txid=txid,
                             state=Transaction.TO_SEND,
                             local=True,
                             raw=txdoc.signed_raw())
            return await self._transactions_processor.send(tx, txdoc, connection.currency)
        except NotEnoughChangeError as e:
            return (False, str(e)), None
