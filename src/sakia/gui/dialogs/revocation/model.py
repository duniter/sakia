from duniterpy.documents.certification import Revocation
from duniterpy.api import bma, errors
from PyQt5.QtCore import QObject
import aiohttp


class RevocationModel(QObject):
    """
    The model of HomeScreen component
    """

    def __init__(self, parent, app, account):
        super().__init__(parent)
        self.app = app
        self.account = account

        self.revocation_document = None
        self.revoked_selfcert = None

    def load_revocation(self, path):
        """
        Load a revocation document from a file
        :param str path:
        """
        with open(path, 'r') as file:
            file_content = file.read()
            self.revocation_document = Revocation.from_signed_raw(file_content)
            self.revoked_selfcert = Revocation.extract_self_cert(file_content)

    def communities_names(self):
        return [c.name for c in self.account.communities]

    async def send_to_community(self, index):
        community = self.account.communities[index]
        responses = await community.bma_access.broadcast(bma.wot.Revoke, {},
                                       {
                                           'revocation': self.revocation_document.signed_raw(
                                               self.revoked_selfcert)
                                       })

        result = False, ""
        for r in responses:
            if r.status == 200:
                result = True, (await r.json())
            elif not result[0]:
                result = False, (await r.text())
            else:
                await r.release()

        return result

    async def send_to_node(self, server, port):
        session = aiohttp.ClientSession()
        try:
            node = await Node.from_address(None, server, port, proxy=self.app.parameters.proxy(), session=session)
            conn_handler = node.endpoint.conn_handler()
            await bma.wot.Revoke(conn_handler).post(session,
                                                    revocation=self.revocation_document.signed_raw(
                                                        self.revoked_selfcert))
        except (ValueError, errors.DuniterError,
                aiohttp.errors.ClientError, aiohttp.errors.DisconnectedError,
                aiohttp.errors.TimeoutError) as e:
            return False, str(e)
        finally:
            session.close()
        return True, ""
