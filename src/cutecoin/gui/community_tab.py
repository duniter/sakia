'''
Created on 2 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QWidget, QMessageBox, QAction, QMenu, QDialog, \
                            QAbstractItemView
from cutecoin.models.identities import IdentitiesFilterProxyModel, IdentitiesTableModel
from ..gen_resources.community_tab_uic import Ui_CommunityTabWidget
from cutecoin.gui.contact import ConfigureContactDialog
from cutecoin.gui.member import MemberDialog
from .wot_tab import WotTabWidget
from .transfer import TransferMoneyDialog
from .password_asker import PasswordAskerDialog
from .certification import CertificationDialog
from ..tools.exceptions import PersonNotFoundError, NoPeerAvailable
from ..core.person import Person
from ucoinpy.api import bma


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
        self.setupUi(self)
        self.parent = parent
        self.community = community
        self.account = account
        self.password_asker = password_asker
        identities_model = IdentitiesTableModel(community)
        proxy = IdentitiesFilterProxyModel()
        proxy.setSourceModel(identities_model)
        self.table_identities.setModel(proxy)
        self.table_identities.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_identities.customContextMenuRequested.connect(self.identity_context_menu)
        self.table_identities.sortByColumn(0, Qt.AscendingOrder)

        if self.account.member_of(self.community):
            self.button_membership.setText("Renew membership")
        else:
            self.button_membership.setText("Send membership demand")
            self.button_leaving.hide()

        self.wot_tab = WotTabWidget(app, account, community, password_asker, self)
        self.tabs_information.addTab(self.wot_tab, QIcon(':/icons/wot_icon'), "WoT")
        self.refresh()

    def identity_context_menu(self, point):
        index = self.table_identities.indexAt(point)
        model = self.table_identities.model()
        if index.row() < model.rowCount():
            source_index = model.mapToSource(index)
            pubkey_col = model.sourceModel().columns_ids.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                   pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            identity = Person.lookup(pubkey, self.community)
            menu = QMenu(self)

            informations = QAction("Informations", self)
            informations.triggered.connect(self.menu_informations)
            informations.setData(identity)

            add_contact = QAction("Add as contact", self)
            add_contact.triggered.connect(self.menu_add_as_contact)
            add_contact.setData(identity)

            send_money = QAction("Send money", self)
            send_money.triggered.connect(self.menu_send_money)
            send_money.setData(identity)

            certify = QAction("Certify identity", self)
            certify.triggered.connect(self.menu_certify_member)
            certify.setData(identity)

            view_wot = QAction("View in WoT", self)
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

    def certify_identity(self, person):
        dialog = CertificationDialog(self.account, self.password_asker)
        dialog.combo_community.setCurrentText(self.community.name)
        dialog.edit_pubkey.setText(person.pubkey)
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

    def send_membership_demand(self):
        password = self.password_asker.exec_()
        if self.password_asker.result() == QDialog.Rejected:
            return

        try:
            self.account.send_membership(password, self.community, 'IN')
            QMessageBox.information(self, self.tr("Membership"),
                                 self.tr("Success sending membership demand"))
        except ValueError as e:
            QMessageBox.critical(self, self.tr("Join demand error"),
                              str(e))
        except PersonNotFoundError as e:
            QMessageBox.critical(self, self.tr("Key not sent to community"),
                              self.tr("Your key wasn't sent in the community. \
                              You can't request a membership."))
        except NoPeerAvailable as e:
            QMessageBox.critical(self, self.tr("Network error"),
                                 self.tr("Couldn't connect to network : {0}").format(e),
                                 QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 "{0}".format(e),
                                 QMessageBox.Ok)

    def send_membership_leaving(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
Sending a membership demand  cannot be canceled.
The process to join back the community later will have to be done again.""")
.format(self.account.pubkey), QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            password_asker = PasswordAskerDialog(self.app.current_account)
            password = password_asker.exec_()
            if password_asker.result() == QDialog.Rejected:
                return

            try:
                self.account.send_membership(password, self.community, 'OUT')
                QMessageBox.information(self, self.tr("Membership"),
                                     self.tr("Success sending leaving demand"))
            except ValueError as e:
                QMessageBox.critical(self, self.tr("Leaving demand error"),
                                  e.message)
            except NoPeerAvailable as e:
                QMessageBox.critical(self, self.tr("Network error"),
                                     self.tr("Couldn't connect to network : {0}").format(e),
                                     QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"),
                                     "{0}".format(e),
                                     QMessageBox.Ok)

    def search(self):
        """
        Search nodes when return is pressed in combobox lineEdit
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
            persons.append(identity['pubkey'])

        self.edit_textsearch.clear()
        self.refresh(persons)


    def refresh(self, persons=None):
        '''
        Refresh the table with specified identities.
        If no identities is passed, use the account connections.
        '''
        if persons is None:
            self_identity = Person.lookup(self.account.pubkey, self.community)
            account_connections = []
            persons = []
            for p in self_identity.unique_valid_certifiers_of(self.community):
                account_connections.append(Person.lookup(p['pubkey'], self.community))
                persons = [p for p in account_connections
                          if p.pubkey not in [i.pubkey for i in persons]]
            for p in self_identity.unique_valid_certified_by(self.community):
                account_connections.append(Person.lookup(p['pubkey'], self.community))
                persons = persons + [p for p in account_connections
                          if p.pubkey not in [i.pubkey for i in persons]]

        self.table_identities.model().sourceModel().refresh_identities(persons)

    def refresh_person(self, pubkey):
        if self is None:
            logging.error("community_tab self is None in refresh_person. Watcher connected to a destroyed tab")
        else:
            index = self.table_identities.model().sourceModel().person_index(pubkey)
            self.table_identities.model().sourceModel().dataChanged.emit(index[0], index[1])
