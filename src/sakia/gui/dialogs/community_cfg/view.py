from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from .community_cfg_uic import Ui_CommunityConfigurationDialog
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox
import asyncio


class CommunityConfigView(QDialog, Ui_CommunityConfigurationDialog):
    """
    community config view
    """

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)
        self.set_steps_buttons_visible(False)

    def set_creation_layout(self):
        self.setWindowTitle(self.tr("Add a community"))

    def set_edition_layout(self, name):
        self.stacked_pages.removeWidget(self.page_node)
        self.setWindowTitle(self.tr("Configure community {0}").format(name))

    def display_info(self, info):
        self.label_error.setText(info)

    def node_parameters(self):
        server = self.lineedit_server.text()
        port = self.spinbox_port.value()
        return server, port

    def add_node_parameters(self):
        server = self.lineedit_add_address.text()
        port = self.spinbox_add_port.value()
        return server, port

    async def show_success(self, notification):
        if notification:
            toast.display(self.tr("UID broadcast"), self.tr("Identity broadcasted to the network"))
        else:
            await QAsyncMessageBox.information(self, self.tr("UID broadcast"),
                                               self.tr("Identity broadcasted to the network"))

    def show_error(self, notification, error_txt):
        if notification:
            toast.display(self.tr("UID broadcast"), error_txt)
        self.label_error.setText(self.tr("Error") + " " + error_txt)

    def set_steps_buttons_visible(self, visible):
        self.button_next.setVisible(visible)
        self.button_previous.setVisible(visible)

    def set_nodes_model(self, model):
        self.tree_peers.setModel(model)

    def async_exec(self):
        future = asyncio.Future()
        self.finished.connect(lambda r: future.set_result(r))
        self.open()
        return future
