# -*- coding: utf-8 -*-

import time
import datetime
import logging
import copy
from PyQt5.QtWidgets import QWidget, QComboBox
from ..gen_resources.wot_tab_uic import Ui_WotTabWidget
from cutecoin.gui.views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_SELECTED, NODE_STATUS_OUT, ARC_STATUS_STRONG, ARC_STATUS_WEAK
from ucoinpy.api import bma
from cutecoin.core.person import Person


def get_person_from_metadata(metadata):
    return Person(metadata['text'], metadata['id'])


class WotTabWidget(QWidget, Ui_WotTabWidget):
    def __init__(self, account, community, password_asker, parent=None):
        """

        :param cutecoin.core.account.Account account:
        :param cutecoin.core.community.Community community:
        :param parent:
        :return:
        """
        super().__init__(parent)
        self.parent = parent

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
        logging.debug("draw graph !!!!!!!!!!!! - " + metadata['text'])

        # create Person from node metadata
        person = get_person_from_metadata(metadata)
        person_account = Person(self.account.name, self.account.pubkey)
        certifier_list = person.certifiers_of(self.community)
        certified_list = person.certified_by(self.community)

        # reset graph
        graph = dict()

        # add wallet node
        node_status = 0
        if person.pubkey == person_account.pubkey:
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
            'status': node_status,
            'nodes': list()
        }

        # populate graph with certifiers-of
        self.add_certifier_list_to_graph(graph, certifier_list, person, person_account)
        # populate graph with certified-by
        self.add_certified_list_to_graph(graph, certified_list, person, person_account)

        # draw graph in qt scene
        self.graphicsView.scene().update_wot(graph)

        # if selected member is not the account member...
        if person.pubkey != person_account.pubkey:
            # add path from selected member to account member
            path = self.get_path_from_member(graph, person, person_account)
            if path:
                self.graphicsView.scene().update_path(path)

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
        person = get_person_from_metadata(metadata)
        self.parent.certify_member(person)

    def send_money_to_node(self, metadata):
        person = get_person_from_metadata(metadata)
        self.parent.send_money_to_member(person)

    def add_node_as_contact(self, metadata):
        # check if contact already exists...
        if metadata['id'] == self.account.pubkey or metadata['id'] in [contact.pubkey for contact in self.account.contacts]:
            return False
        person = get_person_from_metadata(metadata)
        self.parent.add_member_as_contact(person)

    def get_block_mediantime(self, number):
        try:
            block = self.community.get_block(number)
        except Exception as e:
            logging.debug('community.get_block request error : ' + str(e))
            return False
        return block.mediantime

    def get_path_from_member(self, graph, person_selected, person_account):
        path = list()
        graph_tmp = copy.deepcopy(graph)

        if person_account.pubkey not in graph_tmp.keys():
            # recursively feed graph searching for account node...
            self.feed_graph_to_find_account(graph_tmp, graph_tmp[person_selected.pubkey]['nodes'], person_account, list())
        if len(graph_tmp[person_selected.pubkey]['nodes']) > 0:
            # calculate path of nodes between person and person_account
            path = self.find_shortest_path(graph_tmp, graph_tmp[person_selected.pubkey], graph_tmp[person_account.pubkey])

        if path:
            logging.debug([node['text'] for node in path])
        else:
            logging.debug('no wot path')

        return path

    def feed_graph_to_find_account(self, graph, nodes, person_account, done=list()):
        for node in tuple(nodes):
            if node['id'] in tuple(done):
                continue
            person_selected = Person(node['text'], node['id'])
            certifier_list = person_selected.certifiers_of(self.community)
            self.add_certifier_list_to_graph(graph, certifier_list, person_selected, person_account)
            if person_account.pubkey in tuple(graph.keys()):
                return False
            certified_list = person_selected.certified_by(self.community)
            self.add_certified_list_to_graph(graph, certified_list, person_selected, person_account)
            if person_account.pubkey in tuple(graph.keys()):
                return False
            if node['id'] not in tuple(done):
                done.append(node['id'])
            if len(done) >= len(graph):
                return True
            result = self.feed_graph_to_find_account(graph, graph[person_selected.pubkey]['nodes'], person_account, done)
            if not result:
                return False

        return True

    def find_shortest_path(self, graph, start, end, path=list()):
        path = path + [start]
        if start['id'] == end['id']:
            return path
        if start['id'] not in graph.keys():
            return None
        shortest = None
        for node in tuple(graph[start['id']]['nodes']):
            if node not in path:
                newpath = self.find_shortest_path(graph, node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    def add_certifier_list_to_graph(self, graph, certifiers, person, person_account):

        # add certifiers of uid
        for certifier in tuple(certifiers):
            # add only valid certification...
            if (time.time() - certifier['cert_time']['medianTime']) > self.signature_validity:
                continue
            # new node
            if certifier['pubkey'] not in graph.keys():
                node_status = 0
                if certifier['pubkey'] == person_account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certifier['isMember'] is False:
                    node_status += NODE_STATUS_OUT
                graph[certifier['pubkey']] = {
                    'id': certifier['pubkey'],
                    'arcs': list(),
                    'text': certifier['uid'],
                    'tooltip': certifier['pubkey'],
                    'status': node_status,
                    'nodes': [graph[person.pubkey]]
                }

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
                ).strftime("%d/%m/%Y"),
                'cert_time': certifier['cert_time']['medianTime']
            }
            # add arc to certifier
            graph[certifier['pubkey']]['arcs'].append(arc)
            # if certifier node not in person nodes
            if graph[certifier['pubkey']] not in tuple(graph[person.pubkey]['nodes']):
                # add certifier node to person node
                graph[person.pubkey]['nodes'].append(graph[certifier['pubkey']])

    def add_certified_list_to_graph(self, graph, certified_list, person, person_account):
        # add certified by uid
        for certified in tuple(certified_list):
            # add only valid certification...
            if (time.time() - certified['cert_time']['medianTime']) > self.signature_validity:
                continue
            if certified['pubkey'] not in graph.keys():
                node_status = 0
                if certified['pubkey'] == person_account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certified['isMember'] is False:
                    node_status += NODE_STATUS_OUT
                graph[certified['pubkey']] = {
                    'id': certified['pubkey'],
                    'arcs': list(),
                    'text': certified['uid'],
                    'tooltip': certified['pubkey'],
                    'status': node_status,
                    'nodes': [graph[person.pubkey]]
                }
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
                ).strftime("%d/%m/%Y"),
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
            # if certified node not in person nodes
            if graph[certified['pubkey']] not in tuple(graph[person.pubkey]['nodes']):
                # add certified node to person node
                graph[person.pubkey]['nodes'].append(graph[certified['pubkey']])
