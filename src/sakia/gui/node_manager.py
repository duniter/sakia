import aiohttp

from PyQt5.QtCore import QObject, QEvent, QUrl
from PyQt5.QtWidgets import QDialog

#from ..gen_resources.node_manager_uic import Ui_NodeManager
from .widgets.dialogs import QAsyncMessageBox
from ..tools.decorators import asyncify


class NodeManager(QObject):
    """
    A widget showing informations about a member
    """

    def __init__(self, widget, ui):
        """
        Init MemberDialog

        :param PyQt5.QtWidget widget: The class of the widget
        :param sakia.gen_resources.member_uic.Ui_DialogMember ui: the class of the ui applyed to the widget
        :return:
        """
        super().__init__()
        self.widget = widget
        self.ui = ui
        self.ui.setupUi(self.widget)
        self.widget.installEventFilter(self)

    @classmethod
    def create(cls, parent):
        raise TypeError("Not implemented ( https://github.com/duniter/sakia/issues/399 )")
        #dialog = cls(QDialog(parent), Ui_NodeManager())
        #return dialog

    @asyncify
    async def open_home_page(self):
        try:
            with aiohttp.ClientSession() as session:
                response = await session.get("http://127.0.0.1:9220")
                if response.status == 200:
                    self.ui.web_view.load(QUrl("http://127.0.0.1:9220"))
                    self.ui.web_view.show()
                    self.widget.show()
                else:
                    await QAsyncMessageBox.critical(self.widget, "Local node manager",
                                            "Could not access to local node ui.")
        except aiohttp.ClientError:
            await QAsyncMessageBox.critical(self.widget, "Local node manager",
                                      "Could not connect to node. Please make sure it's running.")

    def eventFilter(self, source, event):
        if event.type() == QEvent.Resize:
            self.widget.resizeEvent(event)
        return self.widget.eventFilter(source, event)

    def exec(self):
        self.widget.exec()
