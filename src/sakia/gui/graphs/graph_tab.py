from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot, QEvent, QLocale, QDateTime, pyqtSignal, QObject
from PyQt5.QtGui import QCursor

from ...tools.exceptions import MembershipNotFoundError
from ...tools.decorators import asyncify, once_at_a_time
from ...core.registry import BlockchainState
from ..widgets.context_menu import ContextMenu


class GraphTabWidget(QObject):

    money_sent = pyqtSignal()

    def __init__(self, app, account=None, community=None, password_asker=None, widget=QWidget):
        """
        :param sakia.core.app.Application app: Application instance
        :param sakia.core.app.Application app: Application instance
        :param sakia.core.Account account: The account displayed in the widget
        :param sakia.core.Community community: The community displayed in the widget
        :param sakia.gui.Password_Asker: password_asker: The widget to ask for passwords
        :param class widget: The class of the graph tab
        """
        super().__init__()

        self.widget = widget()
        self.account = account
        self.community = community
        self.password_asker = password_asker

        self.app = app

    def set_scene(self, scene):
        # add scene events
        scene.node_context_menu_requested.connect(self.node_context_menu)

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

    @asyncify
    async def node_context_menu(self, pubkey):
        """
        Open the node context menu
        :param str pubkey: the pubkey of the node to open
        """
        identity = await self.app.identities_registry.future_find(pubkey, self.community)
        menu = ContextMenu.from_data(self.widget, self.app, self.account, self.community, self.password_asker,
                                     (identity,))

        # Show the context menu.
        menu.qmenu.popup(QCursor.pos())

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
