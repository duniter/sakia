from PyQt5.QtWidgets import QWidget, QDialog
from PyQt5.QtCore import pyqtSlot, QEvent, QLocale, QDateTime, pyqtSignal

from ...tools.exceptions import MembershipNotFoundError
from ...tools.decorators import asyncify, once_at_a_time
from ...core.registry import BlockchainState
from ...gui.member import MemberDialog
from ...gui.certification import CertificationDialog
from ...gui.transfer import TransferMoneyDialog
from ...gui.contact import ConfigureContactDialog


class GraphTabWidget(QWidget):

    money_sent = pyqtSignal()
    def __init__(self, app):
        """
        :param sakia.core.app.Application app: Application instance
        """
        super().__init__()

        self.password_asker = None
        self.app = app

    def set_scene(self, scene):
        # add scene events
        scene.node_clicked.connect(self.handle_node_click)
        scene.node_signed.connect(self.sign_node)
        scene.node_transaction.connect(self.send_money_to_node)
        scene.node_contact.connect(self.add_node_as_contact)
        scene.node_member.connect(self.identity_informations)
        scene.node_copy_pubkey.connect(self.copy_node_pubkey)

    @once_at_a_time
    @asyncify
    async def refresh_informations_frame(self):
        parameters = self.community.parameters
        try:
            identity = await self.account.identity(self.community)
            membership = identity.membership(self.community)
            renew_block = membership['blockNumber']
            last_renewal = self.community.get_block(renew_block)['medianTime']
            expiration = last_renewal + parameters['sigValidity']
        except MembershipNotFoundError:
            last_renewal = None
            expiration = None

        certified = await identity.unique_valid_certified_by(self.app.identities_registry, self.community)
        certifiers = await identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
        if last_renewal and expiration:
            date_renewal = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(last_renewal).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )
            date_expiration = QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(expiration).date(), QLocale.dateFormat(QLocale(), QLocale.LongFormat)
            )

            if self.account.pubkey in self.community.members_pubkeys():
                # set infos in label
                self.label_general.setText(
                    self.tr("""
                    <table cellpadding="5">
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    </table>
                    """).format(
                        self.account.name, self.account.pubkey,
                        self.tr("Membership"),
                        self.tr("Last renewal on {:}, expiration on {:}").format(date_renewal, date_expiration),
                        self.tr("Your web of trust"),
                        self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                    )
                )
            else:
                # set infos in label
                self.label_general.setText(
                    self.tr("""
                    <table cellpadding="5">
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                    </table>
                    """).format(
                        self.account.name, self.account.pubkey,
                        self.tr("Not a member"),
                        self.tr("Last renewal on {:}, expiration on {:}").format(date_renewal, date_expiration),
                        self.tr("Your web of trust"),
                        self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                             len(certified))
                    )
                )
        else:
            # set infos in label
            self.label_general.setText(
                self.tr("""
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></td></tr>
                <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
                </table>
                """).format(
                    self.account.name, self.account.pubkey,
                    self.tr("Not a member"),
                    self.tr("Your web of trust"),
                    self.tr("Certified by {:} members; Certifier of {:} members").format(len(certifiers),
                                                                                         len(certified))
                )
            )

    @pyqtSlot(str, dict)
    def handle_node_click(self, pubkey, metadata):
        self.draw_graph(
            self.app.identities_registry.from_handled_data(
                metadata['text'],
                pubkey,
                None,
                BlockchainState.VALIDATED,
                self.community
            )
        )

    @once_at_a_time
    @asyncify
    async def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Graph node identity
        """
        pass

    @once_at_a_time
    @asyncify
    async def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        pass

    def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        pass

    def identity_informations(self, pubkey, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            pubkey,
            None,
            BlockchainState.VALIDATED,
            self.community
        )
        dialog = MemberDialog(self.app, self.account, self.community, identity)
        dialog.exec_()

    @asyncify
    async def sign_node(self, pubkey, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            pubkey,
            None,
            BlockchainState.VALIDATED,
            self.community
        )
        await CertificationDialog.certify_identity(self.app, self.account, self.password_asker,
                                             self.community, identity)

    @asyncify
    async def send_money_to_node(self, pubkey, metadata):
        identity = self.app.identities_registry.from_handled_data(
            metadata['text'],
            pubkey,
            None,
            BlockchainState.VALIDATED,
            self.community
        )
        result = await TransferMoneyDialog.send_money_to_identity(self.app, self.account, self.password_asker,
                                                            self.community, identity)
        if result == QDialog.Accepted:
            self.money_sent.emit()

    def copy_node_pubkey(self, pubkey):
        cb = self.app.qapp.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(pubkey, mode=cb.Clipboard)

    def add_node_as_contact(self, pubkey, metadata):
        # check if contact already exists...
        if pubkey == self.account.pubkey \
                or pubkey in [contact['pubkey'] for contact in self.account.contacts]:
            return False
        dialog = ConfigureContactDialog(self.account, self.window(), {'name': metadata['text'],
                                                                      'pubkey': pubkey,
                                                                      })
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super().changeEvent(event)
