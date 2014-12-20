# -*- coding: utf-8 -*-

import time
import datetime
from PyQt5.QtWidgets import QWidget

from cutecoin.gen_resources.wot_form_uic import Ui_Form
from cutecoin.wot.qt.view import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_SELECTED, ARC_STATUS_STRONG, ARC_STATUS_WEAK
from ucoinpy.api import bma


class Form(QWidget, Ui_Form):
    def __init__(self, account, community, parent=None):
        """

        :param cutecoin.core.account.Account account:
        :param cutecoin.core.community.Community community:
        :param parent:
        :return:
        """
        super(Form, self).__init__(parent)

        # construct from qtDesigner
        self.setupUi(self)

        # add combobox events
        self.comboBoxSearch.lineEdit().textEdited.connect(self.search)
        self.comboBoxSearch.lineEdit().returnPressed.connect(self.combobox_return_pressed)

        # add scene events
        self.graphicsView.scene().node_signed.connect(self.sign_node)
        self.graphicsView.scene().node_clicked.connect(self.draw_graph)

        self.account = account
        self.community = community
        # nodes list for menu from search
        self.nodes = list()
        self.signature_validity = 86400 * 365
        self.ARC_STATUS_STRONG_time = self.signature_validity - (86400 * 165)
        self.draw_graph(self.account.pubkey)

    def draw_graph(self, public_key):
        """
        Draw community graph centered on public_key identity

        :param public_key: Public key of the identity
        """
        graph = dict()
        # add wallet node
        node_status = (NODE_STATUS_HIGHLIGHTED and (public_key == self.account.pubkey)) or 0
        node_status += NODE_STATUS_SELECTED
        certifiers = self.community.request(bma.wot.CertifiersOf, {'search': public_key})

        graph[public_key] = {'arcs': [], 'text': certifiers['uid'], 'tooltip': public_key, 'status': node_status}

        # add certifiers of uid
        #for certifier in self.community.request(mapi.get_sig_to(public_key):
        for certifier in certifiers['certifications']:
            if (time.time() - certifier['cert_time']['medianTime']) > self.ARC_STATUS_STRONG_time:
                arc_status = ARC_STATUS_WEAK
            else:
                arc_status = ARC_STATUS_STRONG
            arc = {
                'id': public_key,
                'status': arc_status,
                'tooltip': datetime.datetime.fromtimestamp(
                    certifier['cert_time']['medianTime'] + self.signature_validity
                ).strftime("%Y/%m/%d")
            }
            if certifier['pubkey'] not in graph.keys():
                node_status = (NODE_STATUS_HIGHLIGHTED and (certifier['pubkey'] == self.account.pubkey)) or 0
                graph[certifier['pubkey']] = {
                    'arcs': [arc],
                    'text': certifier['uid'],
                    'tooltip': certifier['pubkey'],
                    'status': node_status
                }

        # add certified by uid
        #for certified in mapi.get_sig_from(public_key):
        for certified in self.community.request(bma.wot.CertifiedBy, {'search': public_key})['certifications']:
            if (time.time() - certified['cert_time']['medianTime']) > self.ARC_STATUS_STRONG_time:
                arc_status = ARC_STATUS_WEAK
            else:
                arc_status = ARC_STATUS_STRONG
            arc = {
                'id': certified['pubkey'],
                'status': arc_status,
                'tooltip': datetime.datetime.fromtimestamp(
                    certified['cert_time']['medianTime'] + self.signature_validity
                ).strftime("%Y/%m/%d")
            }
            graph[public_key]['arcs'].append(arc)
            if certified['pubkey'] not in graph.keys():
                node_status = (NODE_STATUS_HIGHLIGHTED and (certified['pubkey'] == self.account.pubkey)) or 0
                graph[certified['pubkey']] = {
                    'arcs': list(),
                    'text': certified['uid'],
                    'tooltip': certified['pubkey'],
                    'status': node_status
                }

        # draw graph in qt scene
        self.graphicsView.scene().update_wot(graph)

    def reset(self):
        """
        Reset graph scene to wallet identity
        """
        self.draw_graph(
            self.account.pubkey
        )

    def combobox_return_pressed(self):
        """
        Search nodes when return is pressed in combobox lineEdit
        """
        self.search(self.comboBoxSearch.lineEdit().text())

    def search(self, text):
        """
        Search nodes when text is edited in combobox lineEdit
        """
        if len(text) < 2:
            return False

        response = self.community.request(bma.wot.Lookup, {'search': text})
        nodes = {}
        for identity in response['results']:
            if identity['uids'][0]['others']:
                nodes[identity['pubkey']] = identity['uids'][0]['uid']

        if nodes:
            self.nodes = list()
            self.comboBoxSearch.clear()
            self.comboBoxSearch.lineEdit().setText(text)
            for pubkey, uid in nodes.items():
                self.nodes.append({'pubkey': pubkey, 'uid': uid})
                self.comboBoxSearch.addItem(uid)
            self.comboBoxSearch.showPopup()

    def select_node(self, index):
        """
        Select node in graph when item is selected in combobox
        """
        if index < 0 or index >= len(self.nodes):
            return False
        node = self.nodes[index]
        self.draw_graph(
                node['pubkey']
        )

    def sign_node(self, public_key):
        print('sign node {} not implemented'.format(public_key))
