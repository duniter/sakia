from duniterpy.documents import Revocation, BMAEndpoint, SecuredBMAEndpoint
from duniterpy.api import bma, errors
from sakia.data.connectors import NodeConnector
from asyncio import TimeoutError
from socket import gaierror
import jsonschema
from aiohttp import ClientError
from PyQt5.QtCore import QObject
import logging


class RevocationModel(QObject):
    """
    The model of HomeScreen component
    """

    def __init__(self, app, connection):
        super().__init__()
        self.app = app
        self.connection = connection

        self.revocation_document = None
        self.revoked_identity = None
        self._logger = logging.getLogger('sakia')

    def load_revocation(self, path):
        """
        Load a revocation document from a file
        :param str path:
        """
        with open(path, 'r') as file:
            file_content = file.read()
            self.revocation_document = Revocation.from_signed_raw(file_content)
            self.revoked_identity = Revocation.extract_self_cert(file_content)

    def currencies_names(self):
        return [c for c in self.app.db.connections_repo.get_currencies()]

    async def broadcast_to_network(self, index):
        currency = self.currencies_names()[index]
        return await self.app.documents_service.broadcast_revocation(currency, self.revoked_identity,
                                                               self.revocation_document)

    async def send_to_node(self, server, port, secured):
        signed_raw = self.revocation_document.signed_raw(self.revoked_identity)
        node_connector = await NodeConnector.from_address(None, secured, server, port, self.app.parameters)
        for endpoint in [e for e in node_connector.node.endpoints
                         if isinstance(e, BMAEndpoint) or isinstance(e, SecuredBMAEndpoint)]:
            try:
                self._logger.debug("Broadcasting : \n" + signed_raw)
                conn_handler = endpoint.conn_handler(node_connector.session, proxy=self.app.parameters.proxy())
                result = await bma.wot.revoke(conn_handler, signed_raw)
                if result.status == 200:
                    return True, ""
                else:
                    return False, bma.api.parse_error(await result.text())["message"]
            except errors.DuniterError as e:
                return False, e.message
            except (jsonschema.ValidationError, ClientError, gaierror,
                    TimeoutError, ConnectionRefusedError, ValueError) as e:
                return False, str(e)
            finally:
                node_connector.session.close()
        return True, ""
