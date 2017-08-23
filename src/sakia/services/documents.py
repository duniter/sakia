import jsonschema
import attr
import logging

from duniterpy.key import SigningKey
from duniterpy.documents import Certification, Membership, Revocation, InputSource, \
    OutputSource, SIGParameter, Unlock, block_uid, BlockUID
from duniterpy.documents import Identity as IdentityDoc
from duniterpy.documents import Transaction as TransactionDoc
from duniterpy.documents.transaction import reduce_base
from duniterpy.grammars import output
from duniterpy.api import bma
from sakia.data.entities import Identity, Transaction, Source
from sakia.data.processors import BlockchainProcessor, IdentitiesProcessor, NodesProcessor, \
    TransactionsProcessor, SourcesProcessor, CertificationsProcessor
from sakia.data.connectors import BmaConnector, parse_bma_responses
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
    _certifications_processor = attr.ib()
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
                   CertificationsProcessor.instanciate(app),
                   TransactionsProcessor.instanciate(app),
                   SourcesProcessor.instanciate(app))

    def generate_identity(self, connection):
        identity = self._identities_processor.get_identity(connection.currency, connection.pubkey, connection.uid)
        if not identity:
            identity = Identity(connection.currency, connection.pubkey, connection.uid)

        sig_window = self._blockchain_processor.parameters(connection.currency).sig_window
        current_time = self._blockchain_processor.time(connection.currency)

        if identity.is_obsolete(sig_window, current_time):
            block_uid = self._blockchain_processor.current_buid(connection.currency)
            identity.blockstamp = block_uid
            timestamp = self._blockchain_processor.time(connection.currency)
            identity.timestamp = timestamp
            identity.signature = None

        return identity

    async def broadcast_identity(self, connection, identity_doc):
        """
        Send our self certification to a target community

        :param sakia.data.entities.Connection connection: the connection published
        """
        self._logger.debug("Key publish : {0}".format(identity_doc.signed_raw()))

        responses = await self._bma_connector.broadcast(connection.currency, bma.wot.add,
                                                        req_args={'identity': identity_doc.signed_raw()})
        result = await parse_bma_responses(responses)

        return result

    async def broadcast_revocation(self, currency, identity_document, revocation_document):
        signed_raw = revocation_document.signed_raw(identity_document)
        self._logger.debug("Broadcasting : \n" + signed_raw)
        responses = await self._bma_connector.broadcast(currency, bma.wot.revoke, req_args={
                                                            'revocation': signed_raw
                                                        })

        result = False, ""
        for r in responses:
            if r.status == 200:
                result = True, (await r.json())
            elif not result[0]:
                try:
                    result = False, bma.api.parse_error(await r.text())["message"]
                except jsonschema.ValidationError as e:
                    result = False, str(e)
            else:
                await r.release()

        return result

    async def send_membership(self, connection, secret_key, password, mstype):
        """
        Send a membership document to a target community.
        Signal "document_broadcasted" is emitted at the end.

        :param sakia.data.entities.Connection connection: the connection publishing ms doc
        :param str secret_key: The account SigningKey salt
        :param str password: The account SigningKey password
        :param str mstype: The type of membership demand. "IN" to join, "OUT" to leave
        """
        self._logger.debug("Send membership")

        blockUID = self._blockchain_processor.current_buid(connection.currency)
        membership = Membership(10, connection.currency,
                                connection.pubkey, blockUID, mstype, connection.uid,
                                connection.blockstamp, None)
        key = SigningKey(secret_key, password, connection.scrypt_params)
        membership.sign([key])
        self._logger.debug("Membership : {0}".format(membership.signed_raw()))
        responses = await self._bma_connector.broadcast(connection.currency, bma.blockchain.membership,
                                                        req_args={'membership': membership.signed_raw()})
        result = await parse_bma_responses(responses)

        return result

    async def certify(self, connection, secret_key, password, identity):
        """
        Certify an other identity

        :param sakia.data.entities.Connection connection: the connection published
        :param str secret_key: the private key salt
        :param str password: the private key password
        :param sakia.data.entities.Identity identity: the identity certified
        """
        self._logger.debug("Certdata")
        blockUID = self._blockchain_processor.current_buid(connection.currency)
        if not identity.signature:
            lookup_data = await self._bma_connector.get(connection.currency, bma.wot.lookup,
                                                     req_args={'search': identity.pubkey})
            for uid_data in next(data["uids"] for data in lookup_data["results"] if data["pubkey"] == identity.pubkey):
                if uid_data["uid"] == identity.uid and block_uid(uid_data["meta"]["timestamp"]) == identity.blockstamp:
                    identity.signature = uid_data["self"]
                    break
            else:
                return False, "Could not find certified identity signature"

        certification = Certification(10, connection.currency,
                                      connection.pubkey, identity.pubkey, blockUID, None)

        key = SigningKey(secret_key, password, connection.scrypt_params)
        certification.sign(identity.document(), [key])
        signed_cert = certification.signed_raw(identity.document())
        self._logger.debug("Certification : {0}".format(signed_cert))
        timestamp = self._blockchain_processor.time(connection.currency)
        responses = await self._bma_connector.broadcast(connection.currency, bma.wot.certify, req_args={'cert': signed_cert})
        result = await parse_bma_responses(responses)
        if result[0]:
            self._identities_processor.insert_or_update_identity(identity)
            self._certifications_processor.create_or_update_certification(connection.currency, certification,
                                                                          timestamp, None)

        return result

    async def revoke(self, currency, identity, salt, password):
        """
        Revoke self-identity on server, not in blockchain

        :param str currency: The currency of the identity
        :param sakia.data.entities.IdentityDoc identity: The certified identity
        :param str salt: The account SigningKey salt
        :param str password: The account SigningKey password
        """
        revocation = Revocation(10, currency, None)
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
        result = await parse_bma_responses(responses)
        return result

    def generate_revocation(self, connection, secret_key, password):
        """
        Generate account revocation document for given community

        :param sakia.data.entities.Connection connection: The connection of the identity
        :param str secret_key: The account SigningKey secret key
        :param str password: The account SigningKey password
        """
        document = Revocation(10, connection.currency, connection.pubkey, "")
        identity = self._identities_processor.get_identity(connection.currency, connection.pubkey, connection.uid)
        if not identity:
            identity = self.generate_identity(connection)
            identity_doc = identity.document()
            key = SigningKey(connection.salt, connection.password, connection.scrypt_params)
            identity_doc.sign([key])
            identity.signature = identity_doc.signatures[0]
            self._identities_processor.insert_or_update_identity(identity)

        self_cert = identity.document()

        key = SigningKey(secret_key, password, connection.scrypt_params)

        document.sign(self_cert, [key])
        return document.signed_raw(self_cert), identity

    def tx_sources(self, amount, amount_base, currency, pubkey):
        """
        Get inputs to generate a transaction with a given amount of money
        :param int amount: The amount target value
        :param int amount_base: The amount base target value
        :param str currency: The community target of the transaction
        :param str pubkey: The pubkey owning the sources
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
        available_sources = self._sources_processor.available(currency, pubkey)
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

    def commit_outputs_to_self(self, currency, pubkey, txdoc):
        """
        Save outputs to self
        :param str currency:
        :param str pubkey:
        :param TransactionDoc txdoc:
        :return:
        """
        for offset, output in enumerate(txdoc.outputs):
            if output.conditions.left.pubkey == pubkey:
                source = Source(currency=currency,
                                pubkey=pubkey,
                                identifier=txdoc.sha_hash,
                                type='T',
                                noffset=offset,
                                amount=output.amount,
                                base=output.base)
                self._sources_processor.insert(source)

    def prepare_tx(self, key, receiver, blockstamp, amount, amount_base, message, currency):
        """
        Prepare a simple Transaction document
        :param SigningKey key: the issuer of the transaction
        :param str receiver: the target of the transaction
        :param duniterpy.documents.BlockUID blockstamp: the blockstamp
        :param int amount: the amount sent to the receiver
        :param int amount_base: the amount base of the currency
        :param str message: the comment of the tx
        :param str currency: the target community
        :return: the transaction document
        :rtype: List[sakia.data.entities.Transaction]
        """
        forged_tx = []
        sources = [None]*41
        while len(sources) > 40:
            result = self.tx_sources(int(amount), amount_base, currency, key.pubkey)
            sources = result[0]
            computed_outputs = result[1]
            overheads = result[2]
            # Fix issue #594
            if len(sources) > 40:
                sources_value = 0
                for s in sources[:39]:
                    sources_value += s.amount * (10**s.base)
                sources_value, sources_base = reduce_base(sources_value, 0)
                chained_tx = self.prepare_tx(key, key.pubkey, blockstamp,
                                             sources_value, sources_base, "[CHAINED]", currency)
                forged_tx += chained_tx
        self._sources_processor.consume(sources)
        logging.debug("Inputs : {0}".format(sources))

        inputs = self.tx_inputs(sources)
        unlocks = self.tx_unlocks(sources)
        outputs = self.tx_outputs(key.pubkey, receiver, computed_outputs, overheads)
        logging.debug("Outputs : {0}".format(outputs))
        txdoc = TransactionDoc(10, currency, blockstamp, 0,
                               [key.pubkey], inputs, unlocks,
                               outputs, message, None)
        txdoc.sign([key])
        self.commit_outputs_to_self(currency, key.pubkey, txdoc)
        time = self._blockchain_processor.time(currency)
        tx = Transaction(currency=currency,
                         pubkey=key.pubkey,
                         sha_hash=txdoc.sha_hash,
                         written_block=0,
                         blockstamp=blockstamp,
                         timestamp=time,
                         signatures=txdoc.signatures,
                         issuers=[key.pubkey],
                         receivers=[receiver],
                         amount=amount,
                         amount_base=amount_base,
                         comment=txdoc.comment,
                         txid=0,
                         state=Transaction.TO_SEND,
                         local=True,
                         raw=txdoc.signed_raw())
        forged_tx.append(tx)
        return forged_tx

    async def send_money(self, connection, secret_key, password, recipient, amount, amount_base, message):
        """
        Send money to a given recipient in a specified community
        :param sakia.data.entities.Connection connection: The account salt
        :param str secret_key: The account secret_key
        :param str password: The account password
        :param str recipient: The pubkey of the recipient
        :param int amount: The amount of money to transfer
        :param int amount_base: The amount base of the transfer
        :param str message: The message to send with the transfer
        """
        blockstamp = self._blockchain_processor.current_buid(connection.currency)
        key = SigningKey(secret_key, password, connection.scrypt_params)
        logging.debug("Sender pubkey:{0}".format(key.pubkey))
        tx_entities = []
        result = (True, ""), tx_entities
        try:
            tx_entities = self.prepare_tx(key, recipient, blockstamp, amount, amount_base,
                                           message, connection.currency)

            for i, tx in enumerate(tx_entities):
                logging.debug("Transaction : [{0}]".format(tx.raw))
                tx.txid = i
                tx_res, tx_entities[i] = await self._transactions_processor.send(tx, connection.currency)

                # Result can be negative if a tx is not accepted by the network
                if result[0]:
                    if not tx_res[0]:
                        result = (False, tx_res[1]), tx_entities
                result = result[0], tx_entities
            return result
        except NotEnoughChangeError as e:
            return (False, str(e)), tx_entities
