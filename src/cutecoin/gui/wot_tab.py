# -*- coding: utf-8 -*-

import time
import datetime
import logging
from PyQt5.QtWidgets import QWidget, QComboBox, QDialog

from ..gen_resources.wot_tab_uic import Ui_WotTabWidget
from cutecoin.gui.views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_SELECTED, NODE_STATUS_OUT, ARC_STATUS_STRONG, ARC_STATUS_WEAK
from ucoinpy.api import bma
from .certification import CertificationDialog
from cutecoin.gui.contact import ConfigureContactDialog
from .transfer import TransferMoneyDialog
from cutecoin.core.person import Person


class WotTabWidget(QWidget, Ui_WotTabWidget):
    def __init__(self, account, community, password_asker, parent=None):
        """

        :param cutecoin.core.account.Account account:
        :param cutecoin.core.community.Community community:
        :param parent:
        :return:
        """
        super().__init__(parent)

        # construct from qtDesigner
        self.setupUi(self)

        # add combobox events
        self.comboBoxSearch.lineEdit().returnPressed.connect(self.search)
        # To fix a recall of the same item with different case,
        # the edited text is not added in the item list
        self.comboBoxSearch.setInsertPolicy(QComboBox.NoInsert)

        # add scene events
        self.graphicsView.scene().node_clicked.connect(self.draw_graph)
        self.graphicsView.scene().node_signed.connect(self.sign_node)
        self.graphicsView.scene().node_transaction.connect(self.send_money_to_node)
        self.graphicsView.scene().node_contact.connect(self.add_node_as_contact)

        self.account = account
        self.community = community
        self.password_asker = password_asker

        # nodes list for menu from search
        self.nodes = list()
        self.signature_validity = self.community.get_parameters()['sigValidity']
        # arc considered strong during 75% of signature validity time
        self.ARC_STATUS_STRONG_time = int(self.signature_validity * 0.75)

        # create node metadata from account
        metadata = {'text': self.account.name, 'id': self.account.pubkey}
        self.draw_graph(metadata)

    def draw_graph(self, metadata):
        """
        Draw community graph centered on the identity

        :param dict metadata: Graph node metadata of the identity
        """
        # create Person from node metadata
        person = Person(metadata['text'], metadata['id'])
        certifiers = person.certifiers_of(self.community)

        # reset graph
        graph = dict()

        # add wallet node
        node_status = 0
        if person.pubkey == self.account.pubkey:
            node_status += NODE_STATUS_HIGHLIGHTED
        if person.is_member(self.community) is False:
            node_status += NODE_STATUS_OUT
        node_status += NODE_STATUS_SELECTED

        # center node
        graph[person.pubkey] = {
            'id': person.pubkey,
            'arcs': list(),
            'text': person.name,
            'tooltip':  person.pubkey,
            'status': node_status
        }

        # add certifiers of uid
        for certifier in certifiers:
            # new node
            if certifier['pubkey'] not in graph.keys():
                node_status = 0
                if certifier['pubkey'] == self.account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certifier['isMember'] is False:
                    node_status += NODE_STATUS_OUT
                graph[certifier['pubkey']] = {
                    'id': certifier['pubkey'],
                    'arcs': list(),
                    'text': certifier['uid'],
                    'tooltip': certifier['pubkey'],
                    'status': node_status
                }
            # add only valid certification...
            if (time.time() - certifier['cert_time']['medianTime']) > self.signature_validity:
                continue
            # keep only the latest certification
            if graph[certifier['pubkey']]['arcs']:
                if certifier['cert_time']['medianTime'] < graph[certifier['pubkey']]['arcs'][0]['cert_time']:
                    continue
                # display validity status
            if (time.time() - certifier['cert_time']['medianTime']) > self.ARC_STATUS_STRONG_time:
                arc_status = ARC_STATUS_WEAK
            else:
                arc_status = ARC_STATUS_STRONG
            arc = {
                'id': person.pubkey,
                'status': arc_status,
                'tooltip': datetime.datetime.fromtimestamp(
                    certifier['cert_time']['medianTime'] + self.signature_validity
                ).strftime("%Y/%m/%d"),
                'cert_time': certifier['cert_time']['medianTime']
            }
            graph[certifier['pubkey']]['arcs'] = [arc]

        # add certified by uid
        for certified in person.certified_by(self.community):
            if certified['pubkey'] not in graph.keys():
                node_status = 0
                if certified['pubkey'] == self.account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certified['isMember'] is False:
                    node_status += NODE_STATUS_OUT

                graph[certified['pubkey']] = {
                    'id': certified['pubkey'],
                    'arcs': list(),
                    'text': certified['uid'],
                    'tooltip': certified['pubkey'],
                    'status': node_status
                }
            # add only valid certification...
            if (time.time() - certified['cert_time']['medianTime']) > self.signature_validity:
                continue
            # display validity status
            if (time.time() - certified['cert_time']['medianTime']) > self.ARC_STATUS_STRONG_time:
                arc_status = ARC_STATUS_WEAK
            else:
                arc_status = ARC_STATUS_STRONG
            arc = {
                'id': certified['pubkey'],
                'status': arc_status,
                'tooltip': datetime.datetime.fromtimestamp(
                    certified['cert_time']['medianTime'] + self.signature_validity
                ).strftime("%Y/%m/%d"),
                'cert_time': certified['cert_time']['medianTime']
            }

            # replace old arc if this one is more recent
            new_arc = True
            index = 0
            for a in graph[person.pubkey]['arcs']:
                # if same arc already exists...
                if a['id'] == arc['id']:
                    # if arc more recent, dont keep old one...
                    if arc['cert_time'] >= a['cert_time']:
                        graph[person.pubkey]['arcs'][index] = arc
                    new_arc = False
                index += 1

            # if arc not in graph...
            if new_arc:
                # add arc in graph
                graph[person.pubkey]['arcs'].append(arc)

        # draw graph in qt scene
        self.graphicsView.scene().update_wot(graph)

    def reset(self):
        """
        Reset graph scene to wallet identity
        """
        metadata = {'text': self.account.name, 'id': self.account.pubkey}
        self.draw_graph(
            metadata
        )

    def search(self):
        """
        Search nodes when return is pressed in combobox lineEdit
        """
        text = self.comboBoxSearch.lineEdit().text()

        if len(text) < 2:
            return False
        try:
            response = self.community.request(bma.wot.Lookup, {'search': text})
        except Exception as e:
            logging.debug('bma.wot.Lookup request error : ' + str(e))
            return False

        nodes = {}
        for identity in response['results']:
            nodes[identity['pubkey']] = identity['uids'][0]['uid']

        if nodes:
            self.nodes = list()
            self.comboBoxSearch.clear()
            self.comboBoxSearch.lineEdit().setText(text)
            for pubkey, uid in nodes.items():
                self.nodes.append({'pubkey': pubkey, 'uid': uid})
                self.comboBoxSearch.addItem(uid)
            self.comboBoxSearch.showPopup()

        if len(nodes) == 1:
            node = self.nodes[0]
            metadata = {'id': node['pubkey'], 'text': node['uid']}
            self.draw_graph(
                metadata
            )

    def select_node(self, index):
        """
        Select node in graph when item is selected in combobox
        """
        if index < 0 or index >= len(self.nodes):
            return False
        node = self.nodes[index]
        metadata = {'id': node['pubkey'], 'text': node['uid']}
        self.draw_graph(
            metadata
        )

    def sign_node(self, metadata):
        # open certify dialog
        dialog = CertificationDialog(self.account, self.password_asker)
        dialog.combo_community.setCurrentText(self.community.name())
        dialog.edit_pubkey.setText(metadata['id'])
        dialog.radio_pubkey.setChecked(True)
        dialog.combo_community.setCurrentText(self.community.name())
        dialog.exec_()

    def send_money_to_node(self, metadata):
        dialog = TransferMoneyDialog(self.account, self.password_asker)
        dialog.edit_pubkey.setText(metadata['id'])
        dialog.combo_community.setCurrentText(self.community.name())
        dialog.radio_pubkey.setChecked(True)

        if dialog.exec_() == QDialog.Accepted:
            currency_tab = self.window().currencies_tabwidget.currentWidget()
            currency_tab.table_history.model().invalidate()

    def add_node_as_contact(self, metadata):
        # check if contact already exists...
        if metadata['id'] == self.account.pubkey or metadata['id'] in [contact.pubkey for contact in self.account.contacts]:
            return False
        dialog = ConfigureContactDialog(self.account, self.window())
        dialog.edit_name.setText(metadata['text'])
        dialog.edit_pubkey.setText(metadata['id'])
        dialog.exec_()

    def get_block_mediantime(self, number):
        try:
            block = self.community.get_block(number)
        except Exception as e:
            logging.debug('community.get_block request error : ' + str(e))
            return False
        return block.mediantime
