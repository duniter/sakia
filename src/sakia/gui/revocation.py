import asyncio
import aiohttp
import logging
from duniterpy.api import errors
from duniterpy.api import bma
from duniterpy.documents import MalformedDocumentError
from duniterpy.documents.certification import Revocation
from sakia.core.net import Node
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5.QtCore import QObject

from .widgets.dialogs import QAsyncMessageBox
from ..tools.decorators import asyncify
from ..gen_resources.revocation_uic import Ui_RevocationDialog


class RevocationDialog(QObject):
    """
    A dialog to revoke an identity
    """

    def __init__(self, app, account, widget, ui):
        """
        Constructor if a certification dialog

        :param sakia.core.Application app:
        :param sakia.core.Account account:
        :param PyQt5.QtWidgets widget: the widget of the dialog
        :param sakia.gen_resources.revocation_uic.Ui_RevocationDialog ui: the view of the certification dialog
        :return:
        """
        super().__init__()
        self.widget = widget
        self.ui = ui
        self.ui.setupUi(self.widget)
        self.app = app
        self.account = account
        self.revocation_document = None
        self.revoked_selfcert = None
        self._steps = (
            {
                'page': self.ui.page_load_file,
                'init': self.init_dialog,
                'next': self.revocation_selected
            },
            {
                'page': self.ui.page_destination,
                'init': self.init_publication_page,
                'next': self.publish
            }
        )
        self._current_step = 0
        self.handle_next_step(init=True)
        self.ui.button_next.clicked.connect(lambda checked: self.handle_next_step(False))

    def handle_next_step(self, init=False):
        if self._current_step < len(self._steps) - 1:
            if not init:
                self.ui.button_next.clicked.disconnect(self._steps[self._current_step]['next'])
                self._current_step += 1
            self._steps[self._current_step]['init']()
            self.ui.stackedWidget.setCurrentWidget(self._steps[self._current_step]['page'])
            self.ui.button_next.clicked.connect(self._steps[self._current_step]['next'])

    def init_dialog(self):
        self.ui.button_next.setEnabled(False)
        self.ui.button_load.clicked.connect(self.load_from_file)

        self.ui.radio_address.toggled.connect(lambda c: self.publication_mode_changed("address"))
        self.ui.radio_community.toggled.connect(lambda c: self.publication_mode_changed("community"))
        self.ui.edit_address.textChanged.connect(self.refresh)
        self.ui.spinbox_port.valueChanged.connect(self.refresh)
        self.ui.combo_community.currentIndexChanged.connect(self.refresh)

    def publication_mode_changed(self, radio):
        self.ui.edit_address.setEnabled(radio == "address")
        self.ui.spinbox_port.setEnabled(radio == "address")
        self.ui.combo_community.setEnabled(radio == "community")
        self.refresh()

    def load_from_file(self):
        selected_files = QFileDialog.getOpenFileName(self.widget,
                                          self.tr("Load a revocation file"),
                                          "",
                                          self.tr("All text files (*.txt)"))
        selected_file = selected_files[0]
        try:
            with open(selected_file, 'r') as file:
                file_content = file.read()
                self.revocation_document = Revocation.from_signed_raw(file_content)
                self.revoked_selfcert = Revocation.extract_self_cert(file_content)
                self.refresh()
                self.ui.button_next.setEnabled(True)
        except FileNotFoundError:
            pass
        except MalformedDocumentError:
            QMessageBox.critical(self.widget, self.tr("Error loading document"),
                                        self.tr("Loaded document is not a revocation document"),
                                 QMessageBox.Ok)
            self.ui.button_next.setEnabled(False)

    def revocation_selected(self):
        pass

    def init_publication_page(self):
        self.ui.combo_community.clear()
        if self.account:
            for community in self.account.communities:
                self.ui.combo_community.addItem(community.currency)
            self.ui.radio_community.setChecked(True)
        else:
            self.ui.radio_address.setChecked(True)
            self.ui.radio_community.setEnabled(False)

    def publish(self):
        self.ui.button_next.setEnabled(False)
        answer = QMessageBox.warning(self.widget, self.tr("Revocation"),
                                      self.tr("""<h4>The publication of this document will remove your identity from the network.</h4>
<li>
    <li> <b>This identity won't be able to join the targeted community anymore.</b> </li>
    <li> <b>This identity won't be able to generate Universal Dividends anymore.</b> </li>
    <li> <b>This identity won't be able to certify individuals anymore.</b> </li>
</li>
Please think twice before publishing this document.
"""), QMessageBox.Ok | QMessageBox.Cancel)
        if answer == QMessageBox.Ok:
            self.accept()
        else:
            self.ui.button_next.setEnabled(True)

    @asyncify
    async def accept(self):
        try:
            session = aiohttp.ClientSession()
            if self.ui.radio_community.isChecked():
                community = self.account.communities[self.ui.combo_community.currentIndex()]
                await community.bma_access.broadcast(bma.wot.Revoke, {},
                       {
                           'revocation': self.revocation_document.signed_raw(self.revoked_selfcert)
                       })
            elif self.ui.radio_address.isChecked():
                    server = self.ui.edit_address.text()
                    port = self.ui.spinbox_port.value()
                    node = await Node.from_address(None, server, port, session=session)
                    conn_handler = node.endpoint.conn_handler()
                    await bma.wot.Revoke(conn_handler).post(session,
                                                revocation=self.revocation_document.signed_raw(self.revoked_selfcert))
        except (MalformedDocumentError, ValueError, errors.DuniterError,
            aiohttp.errors.ClientError, aiohttp.errors.DisconnectedError,
                aiohttp.errors.TimeoutError) as e:
            await QAsyncMessageBox.critical(self.widget, self.tr("Error broadcasting document"),
                                        str(e))
        else:
            await QAsyncMessageBox.information(self.widget, self.tr("Revocation broadcast"),
                                               self.tr("The document was successfully broadcasted."))
            self.widget.accept()
        finally:
            session.close()

    @classmethod
    def open_dialog(cls, app, account):
        """
        Certify and identity
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :return:
        """
        dialog = cls(app, account, QDialog(), Ui_RevocationDialog())
        dialog.refresh()
        return dialog.exec()

    def refresh(self):
        if self.revoked_selfcert:
            text = self.tr("""
<div>Identity revoked : {uid} (public key : {pubkey}...)</div>
<div>Identity signed on block : {timestamp}</div>
    """.format(uid=self.revoked_selfcert.uid,
               pubkey=self.revoked_selfcert.pubkey[:12],
               timestamp=self.revoked_selfcert.timestamp))

            self.ui.label_revocation_content.setText(text)

            if self.ui.radio_community.isChecked():
                target = self.tr("All nodes of community {name}".format(name=self.ui.combo_community.currentText()))
            elif self.ui.radio_address.isChecked():
                target = self.tr("Address {address}:{port}".format(address=self.ui.edit_address.text(),
                                                                   port=self.ui.spinbox_port.value()))
            else:
                target = ""
            self.ui.label_revocation_info.setText("""
<h4>Revocation document</h4>
<div>{text}</div>
<h4>Publication address</h4>
<div>{target}</div>
""".format(text=text,
           target=target))
        else:
            self.ui.label_revocation_content.setText("")

    def async_exec(self):
        future = asyncio.Future()
        self.widget.finished.connect(lambda r: future.set_result(r))
        self.widget.open()
        self.refresh()
        return future

    def exec(self):
        self.widget.exec()
