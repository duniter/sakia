'''
Created on 2 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QWidget, QMessageBox, QAction, QMenu, QDialog, \
                            QAbstractItemView
from cutecoin.models.identities import IdentitiesFilterProxyModel, IdentitiesTableModel
from ..gen_resources.community_tab_uic import Ui_CommunityTabWidget
from cutecoin.gui.contact import ConfigureContactDialog
from cutecoin.gui.member import MemberDialog
from .wot_tab import WotTabWidget
from .transfer import TransferMoneyDialog
from .certification import CertificationDialog
from . import toast
import quamash
from ..tools.exceptions import LookupFailureError, NoPeerAvailable
from ..core.registry import IdentitiesRegistry
from ucoinpy.api import bma
from ..core.net.api import bma as qtbma


class CommunityTabWidget(QWidget, Ui_CommunityTabWidget):

    '''
    classdocs
    '''

    def __init__(self, app, account, community, password_asker, parent):
        """
        Init
        :param cutecoin.core.account.Account account: Account instance
        :param cutecoin.core.community.Community community: Community instance
        :param cutecoin.gui.password_asker.PasswordAskerDialog password_asker: Password asker dialog
        :param cutecoin.gui.currency_tab.CurrencyTabWidget parent: TabWidget instance
        :return:
        """
        super().__init__()
        self.parent = parent
        self.app = app
        self.community = community
        self.account = account
        self.password_asker = password_asker
        self.setup_ui()

    def setup_ui(self):
        self.setupUi(self)
        identities_model = IdentitiesTableModel(self.community)
        proxy = IdentitiesFilterProxyModel()
        proxy.setSourceModel(identities_model)
        self.table_identities.setModel(proxy)
        self.table_identities.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_identities.customContextMenuRequested.connect(self.identity_context_menu)
        self.table_identities.sortByColumn(0, Qt.AscendingOrder)
        self.table_identities.resizeColumnsToContents()

        self.wot_tab = WotTabWidget(self.app, self.account, self.community, self.password_asker, self)
        self.tabs_information.addTab(self.wot_tab, QIcon(':/icons/wot_icon'), self.tr("Web of Trust"))
        members_action = QAction(self.tr("Members"), self)
        members_action.triggered.connect(self.search_members)
        self.button_search.addAction(members_action)
        direct_connections = QAction(self.tr("Direct connections"), self)
        direct_connections.triggered.connect(self.search_direct_connections)
        self.button_search.addAction(direct_connections)

        self.account.identity(self.community).inner_data_changed.connect(self.handle_account_identity_change)
        self.search_direct_connections()
        self.account.membership_broadcasted.connect(self.display_membership_toast)
        self.refresh_quality_buttons()

    def identity_context_menu(self, point):
        index = self.table_identities.indexAt(point)
        model = self.table_identities.model()
        if index.row() < model.rowCount():
            source_index = model.mapToSource(index)
            pubkey_col = model.sourceModel().columns_ids.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                   pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            identity = self.app.identities_registry.lookup(pubkey, self.community)
            menu = QMenu(self)

            informations = QAction(self.tr("Informations"), self)
            informations.triggered.connect(self.menu_informations)
            informations.setData(identity)
            add_contact = QAction(self.tr("Add as contact"), self)
            add_contact.triggered.connect(self.menu_add_as_contact)
            add_contact.setData(identity)

            send_money = QAction(self.tr("Send money"), self)
            send_money.triggered.connect(self.menu_send_money)
            send_money.setData(identity)

            certify = QAction(self.tr("Certify identity"), self)
            certify.triggered.connect(self.menu_certify_member)
            certify.setData(identity)

            view_wot = QAction(self.tr("View in Web of Trust"), self)
            view_wot.triggered.connect(self.view_wot)
            view_wot.setData(identity)

            menu.addAction(informations)
            menu.addAction(add_contact)
            menu.addAction(send_money)
            menu.addAction(certify)
            menu.addAction(view_wot)

            # Show the context menu.
            menu.exec_(QCursor.pos())

    def menu_informations(self):
        person = self.sender().data()
        self.identity_informations(person)

    def menu_add_as_contact(self):
        person = self.sender().data()
        self.add_identity_as_contact({'name': person.uid,
                                    'pubkey': person.pubkey})

    def menu_send_money(self):
        person = self.sender().data()
        self.send_money_to_identity(person)

    def menu_certify_member(self):
        person = self.sender().data()
        self.certify_identity(person)

    def identity_informations(self, person):
        dialog = MemberDialog(self.account, self.community, person)
        dialog.exec_()

    def add_identity_as_contact(self, person):
        dialog = ConfigureContactDialog(self.account, self.window(), person)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    def send_money_to_identity(self, person):
        if isinstance(person, str):
            pubkey = person
        else:
            pubkey = person.pubkey
        dialog = TransferMoneyDialog(self.account, self.password_asker)
        dialog.edit_pubkey.setText(pubkey)
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.radio_pubkey.setChecked(True)
        if dialog.exec_() == QDialog.Accepted:
            currency_tab = self.window().currencies_tabwidget.currentWidget()
            currency_tab.tab_history.table_history.model().sourceModel().refresh_transfers()

    def certify_identity(self, identity):
        dialog = CertificationDialog(self.account, self.app, self.password_asker)
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.edit_pubkey.setText(identity.pubkey)
        dialog.radio_pubkey.setChecked(True)
        dialog.exec_()

    def view_wot(self):
        person = self.sender().data()
        # redraw WoT with this identity selected
        self.wot_tab.draw_graph({'text': person.uid, 'id': person.pubkey})
        # change page to WoT
        index_community_tab = self.parent.tabs_account.indexOf(self)
        self.parent.tabs_account.setCurrentIndex(index_community_tab)
        index_wot_tab = self.tabs_information.indexOf(self.wot_tab)
        self.tabs_information.setCurrentIndex(index_wot_tab)

    @pyqtSlot()
    def display_membership_toast(self):
        toast.display(self.tr("Membership"), self.tr("Success sending Membership demand"))

    def send_membership_demand(self):
        password = self.password_asker.exec_()
        if self.password_asker.result() == QDialog.Rejected:
            return
        with quamash.QEventLoop(self.app.qapp) as loop:
                loop.run_until_complete(self.account.send_membership(password, self.community, 'IN'))
        # except Exception as e:
        #     QMessageBox.critical(self, "Error",
        #                          "{0}".format(e),
        #                          QMessageBox.Ok)

    def send_membership_leaving(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Sending a leaving demand  cannot be canceled.
The process to join back the community later will have to be done again.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            with quamash.QEventLoop(self.app.qapp) as loop:
                    loop.run_until_complete(self.account.send_membership(password, self.community, 'OUT'))

    def publish_uid(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Publishing your UID can be canceled by Revoke UID.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            try:
                self.account.send_selfcert(password, self.community)
                toast.display(self.tr("UID Publishing"),
                              self.tr("Success publishing your UID"))
            except ValueError as e:
                QMessageBox.critical(self, self.tr("Publish UID error"),
                                  str(e))
            except NoPeerAvailable as e:
                QMessageBox.critical(self, self.tr("Network error"),
                                     self.tr("Couldn't connect to network : {0}").format(e),
                                     QMessageBox.Ok)
            # except Exception as e:
            #     QMessageBox.critical(self, self.tr("Error"),
            #                          "{0}".format(e),
            #                          QMessageBox.Ok)

    def revoke_uid(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                                 self.tr("""Are you sure ?
Revoking your UID can only success if it is not already validated by the network.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password = self.password_asker.exec_()
            if self.password_asker.result() == QDialog.Rejected:
                return

            try:
                self.account.revoke(password, self.community)
                toast.display(self.tr("UID Revoking"),
                              self.tr("Success revoking your UID"))
            except ValueError as e:
                QMessageBox.critical(self, self.tr("Revoke UID error"),
                                  str(e))
            except NoPeerAvailable as e:
                QMessageBox.critical(self, self.tr("Network error"),
                                     self.tr("Couldn't connect to network : {0}").format(e),
                                     QMessageBox.Ok)
            # except Exception as e:
            #     QMessageBox.critical(self, self.tr("Error"),
            #                          "{0}".format(e),
            #                          QMessageBox.Ok)

    def search_text(self):
        """
        Search text and display found identities
        """
        text = self.edit_textsearch.text()

        if len(text) < 2:
            return False
        try:
            response = self.community.request(bma.wot.Lookup, {'search': text})
        except Exception as e:
            logging.debug('bma.wot.Lookup request error : ' + str(e))
            return False

        persons = []
        for identity in response['results']:
            persons.append(self.app.identities_registry(identity['pubkey'], self.community))

        self.edit_textsearch.clear()
        self.refresh(persons)

    @pyqtSlot(str)
    def handle_community_change(self, origin):
        logging.debug("Handle account community {0}".format(origin))
        if origin == qtbma.wot.Members:
            self.search_members()

    @pyqtSlot(str)
    def handle_account_identity_change(self, origin):
        logging.debug("Handle account identity change {0}".format(origin))
        if origin in (str(qtbma.wot.CertifiedBy), str(qtbma.wot.CertifiersOf)):
            self.search_direct_connections()

    def search_members(self):
        """
        Search members of community and display found members
        """
        pubkeys = self.community.members_pubkeys()
        identities = []
        for p in pubkeys:
            identities.append(self.app.identities_registry.lookup(p, self.community))

        self_identity = self.account.identity(self.community)

        try:
            self_identity.inner_data_changed.disconnect(self.handle_account_identity_change)
            self.community.inner_data_changed.connect(self.handle_community_change)
        except TypeError as e:
            if "disconnect() failed" in str(e):
                pass
            else:
                raise

        self.edit_textsearch.clear()
        self.refresh(identities)

    def search_direct_connections(self):
        """
        Search members of community and display found members
        """
        self_identity = self.account.identity(self.community)
        try:
            self.community.inner_data_changed.disconnect(self.handle_community_change)
            self_identity.inner_data_changed.connect(self.handle_account_identity_change)
        except TypeError as e:
            if "disconnect() failed" in str(e):
                logging.debug("Could not disconnect community")
            else:
                raise

        account_connections = []
        for p in self_identity.unique_valid_certifiers_of(self.community):
            account_connections.append(self.app.identities_registry.lookup(p['pubkey'], self.community))
        certifiers_of = [p for p in account_connections]
        for p in self_identity.unique_valid_certified_by(self.community):
            account_connections.append(self.app.identities_registry.lookup(p['pubkey'], self.community))
        certified_by = [p for p in account_connections
                  if p.pubkey not in [i.pubkey for i in certifiers_of]]
        identities = certifiers_of + certified_by
        self.refresh(identities)

    def refresh(self, identities):
        '''
        Refresh the table with specified identities.
        If no identities is passed, use the account connections.
        '''
        self.table_identities.model().sourceModel().refresh_identities(identities)
        self.table_identities.resizeColumnsToContents()

    def refresh_quality_buttons(self):
        try:
            if self.account.identity(self.community).published_uid(self.community):
                logging.debug("UID Published")
                if self.account.identity(self.community).is_member(self.community):
                    self.button_membership.setText(self.tr("Renew membership"))
                    self.button_membership.show()
                    self.button_publish_uid.hide()
                    self.button_leaving.show()
                    self.button_revoke_uid.hide()
                else:
                    logging.debug("Not a member")
                    self.button_membership.setText(self.tr("Send membership demand"))
                    self.button_membership.show()
                    self.button_revoke_uid.show()
                    self.button_leaving.hide()
                    self.button_publish_uid.hide()
            else:
                logging.debug("UID not published")
                self.button_membership.hide()
                self.button_leaving.hide()
                self.button_publish_uid.show()
                self.button_revoke_uid.hide()
        except LookupFailureError:
            self.button_membership.hide()
            self.button_leaving.hide()
            self.button_publish_uid.show()

    @pyqtSlot(str)
    def refresh_person(self, pubkey):
        logging.debug("Refresh person {0}".format(pubkey))
        if self is None:
            logging.error("community_tab self is None in refresh_person. Watcher connected to a destroyed tab")
        else:
            if pubkey == self.account.pubkey:
                self.refresh_quality_buttons()

            index = self.table_identities.model().sourceModel().person_index(pubkey)
            self.table_identities.model().sourceModel().dataChanged.emit(index[0], index[1])
