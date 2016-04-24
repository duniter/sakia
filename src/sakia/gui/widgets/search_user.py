import logging

from PyQt5.QtCore import QEvent, pyqtSignal, QT_TRANSLATE_NOOP, Qt
from PyQt5.QtWidgets import QComboBox, QWidget

from duniterpy.api import bma, errors

from ...tools.decorators import asyncify
from ...tools.exceptions import NoPeerAvailable
from ...core.registry import BlockchainState, Identity
from ...gen_resources.search_user_view_uic import Ui_SearchUserWidget


class SearchUserWidget(QWidget, Ui_SearchUserWidget):
    _search_placeholder = QT_TRANSLATE_NOOP("SearchUserWidget", "Research a pubkey, an uid...")

    identity_selected = pyqtSignal(Identity)
    reset = pyqtSignal()

    def __init__(self, parent):
        """
        :param sakia.core.app.Application app: Application instance
        """
        # construct from qtDesigner
        super().__init__(parent)
        self.setupUi(self)
        # Default text when combo lineEdit is empty
        self.combobox_search.lineEdit().setPlaceholderText(self.tr(SearchUserWidget._search_placeholder))
        #  add combobox events
        self.combobox_search.lineEdit().returnPressed.connect(self.search)
        # To fix a recall of the same item with different case,
        # the edited text is not added in the item list
        self.combobox_search.setInsertPolicy(QComboBox.NoInsert)
        self.combobox_search.activated.connect(self.select_node)
        self.button_reset.clicked.connect(self.reset)
        self.nodes = list()
        self.community = None
        self.account = None
        self.app = None
        self._current_identity = None

    def current_identity(self):
        return self._current_identity

    def init(self, app):
        """
        Initialize the widget
        :param sakia.core.Application app: the application
        """
        self.app = app

    def change_account(self, account):
        self.account = account

    def change_community(self, community):
        self.community = community

    @asyncify
    async def search(self):
        """
        Search nodes when return is pressed in combobox lineEdit
        """
        text = self.combobox_search.lineEdit().text()

        if len(text) < 2:
            return False
        try:
            response = await self.community.bma_access.future_request(bma.wot.Lookup, {'search': text})

            nodes = {}
            for identity in response['results']:
                nodes[identity['pubkey']] = identity['uids'][0]['uid']

            if nodes:
                self.nodes = list()
                self.blockSignals(True)
                self.combobox_search.clear()
                self.combobox_search.lineEdit().setText(text)
                for pubkey, uid in nodes.items():
                    self.nodes.append({'pubkey': pubkey, 'uid': uid})
                    self.combobox_search.addItem(uid)
                self.blockSignals(False)
                self.combobox_search.showPopup()
        except errors.duniterError as e:
            if e.ucode == errors.NO_MATCHING_IDENTITY:
                self.nodes = list()
                self.blockSignals(True)
                self.combobox_search.clear()
                self.blockSignals(False)
                self.combobox_search.showPopup()
            else:
                pass
        except NoPeerAvailable:
            pass

    def select_node(self, index):
        """
        Select node in graph when item is selected in combobox
        """
        if index < 0 or index >= len(self.nodes):
            self._current_identity = None
            return False
        node = self.nodes[index]
        metadata = {'id': node['pubkey'], 'text': node['uid']}
        self._current_identity = self.app.identities_registry.from_handled_data(
                metadata['text'],
                metadata['id'],
                None,
                BlockchainState.VALIDATED,
                self.community
            )
        self.identity_selected.emit(
            self._current_identity
        )

    def retranslateUi(self, widget):
        """
        Retranslate missing widgets from generated code
        """
        self.combobox_search.lineEdit().setPlaceholderText(self.tr(SearchUserWidget._search_placeholder))
        super().retranslateUi(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            return

        super().keyPressEvent(event)
