import logging
import time
import asyncio
from PyQt5.QtCore import QLocale, QDateTime
from ..core.registry import Identity, BlockchainState
from ..tools.decorators import asyncify
from ..tools.exceptions import NoPeerAvailable
from cutecoin.gui.views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_OUT, ARC_STATUS_STRONG, ARC_STATUS_WEAK


class Graph(object):
    def __init__(self, app, community, graph=None):
        """
        Init Graph instance
        :param cutecoin.core.app.Application app: Application instance
        :param cutecoin.core.community.Community community: Community instance
        :param dict graph: Dict of the graph
        :return:
        """
        self.app = app
        self.community = community
        self.signature_validity = 0
        self.ARC_STATUS_STRONG_time = 0
        # graph empty if None parameter
        self._graph = graph or (dict() and (graph is None))

    @asyncio.coroutine
    def refresh_signature_validity(self):
        parameters = yield from self.community.parameters()
        self.signature_validity = parameters['sigValidity']
        #  arc considered strong during 75% of signature validity time
        self.ARC_STATUS_STRONG_time = int(self.signature_validity * 0.75)

    def set(self, graph):
        """
        Set the graph from dict
        :param dict graph:
        :return:
        """
        self._graph = graph

    def get(self):
        """
        Return the graph dict
        :return:
        """
        return self._graph

    @asyncio.coroutine
    def get_shortest_path_between_members(self, from_identity, to_identity):
        """
        Return path list of nodes from from_identity to to_identity
        :param identity from_identity:
        :param identity to_identity:
        :return:
        """
        path = list()

        # if from_identity has no certifications, we can not make a path
        certifier_list = yield from from_identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
        certified_list = yield from from_identity.unique_valid_certified_by(self.app.identities_registry, self.community)
        print (certifier_list, certified_list)
        if not certifier_list and not certified_list:
            logging.debug('from_identity has no certifications : can not calculate wot path')
            return path

        # if to_identity has no certifications, we can not make a path
        certifier_list = yield from to_identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
        certified_list = yield from to_identity.unique_valid_certified_by(self.app.identities_registry, self.community)
        if not certifier_list and not certified_list:
            logging.debug('to_identity has no certifications : can not calculate wot path')
            return path

        logging.debug("path between %s to %s..." % (from_identity.uid, to_identity.uid))
        if from_identity.pubkey not in self._graph.keys():
            self.add_identity(from_identity)
            certifier_list = yield from from_identity.unique_valid_certifiers_of(self.app.identities_registry,
                                                                    self.community)
            yield from self.add_certifier_list(certifier_list, from_identity, to_identity)
            certified_list = yield from from_identity.unique_valid_certified_by(self.app.identities_registry,
                                                                   self.community)
            yield from self.add_certified_list(certified_list, from_identity, to_identity)

        if to_identity.pubkey not in self._graph.keys():
            # recursively feed graph searching for account node...
            yield from self.explore_to_find_member(to_identity,
                                                   self._graph[from_identity.pubkey]['connected'], list())
        if len(self._graph[from_identity.pubkey]['connected']) > 0:
            # calculate path of nodes between identity and to_identity
            path = yield from self.find_shortest_path(self._graph[from_identity.pubkey],
                                                      self._graph[to_identity.pubkey])

        if path:
            logging.debug([node['text'] for node in path])
        else:
            logging.debug('no wot path')

        return path

    @asyncio.coroutine
    def explore_to_find_member(self, identity, connected=None, done=None):
        """
        Scan graph recursively to find identity
        :param identity identity:   identity instance to find
        :param list connected:  Optional, default=None, Pubkey list of the connected nodes
        around the current scanned node
        :param list done:       Optional, default=None, List of node already scanned
        :return:
        """
        # functions keywords args are persistent... Need to reset it with None trick
        connected = connected or (list() and (connected is None))
        done = done or (list() and (done is None))
        logging.debug("search %s in " % identity.uid)
        logging.debug([self._graph[pubkey]['text'] for pubkey in connected])
        # for each pubkey connected...
        for pubkey in tuple(connected):
            # capture node connected
            node = self._graph[pubkey]
            if node['id'] in tuple(done):
                continue
            identity_selected = identity.from_handled_data(node['text'], node['id'], BlockchainState.VALIDATED)
            certifier_list = yield from identity_selected.unique_valid_certifiers_of(self.app.identities_registry,
                                                                                     self.community)
            yield from self.add_certifier_list(certifier_list, identity_selected, identity)
            if identity.pubkey in tuple(self._graph.keys()):
                return False
            certified_list = yield from identity_selected.unique_valid_certified_by(self.app.identities_registry,
                                                                                    self.community)
            yield from self.add_certified_list(certified_list, identity_selected, identity)
            if identity.pubkey in tuple(self._graph.keys()):
                return False
            if node['id'] not in tuple(done):
                done.append(node['id'])
            if len(done) >= len(self._graph):
                return True
            result = yield from self.explore_to_find_member(identity,
                                                            self._graph[identity_selected.pubkey]['connected'],
                                                            done)
            if not result:
                return False

        return True

    @asyncio.coroutine
    def find_shortest_path(self, start, end, path=None):
        """
        Find recursively the shortest path between two nodes
        :param dict start:  Start node
        :param dict end:    End node
        :param list path:   Optional, default=None, List of nodes
        :return:
        """
        path = path or (list() and (path is None))
        path = path + [start]
        if start['id'] == end['id']:
            return path
        if start['id'] not in self._graph.keys():
            return None
        shortest = None
        for pubkey in tuple(self._graph[start['id']]['connected']):
            node = self._graph[pubkey]
            if node not in path:
                newpath = yield from self.find_shortest_path(node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    @asyncio.coroutine
    def add_certifier_list(self, certifier_list, identity, identity_account):
        """
        Add list of certifiers to graph
        :param list certifier_list: List of certifiers from api
        :param identity identity:   identity instance which is certified
        :param identity identity_account:   Account identity instance
        :return:
        """
        if self.community:
            try:
                yield from self.refresh_signature_validity()
                #  add certifiers of uid
                for certifier in tuple(certifier_list):
                    # add only valid certification...
                    if (time.time() - certifier['cert_time']) > self.signature_validity:
                        continue
                    # new node
                    if certifier['identity'].pubkey not in self._graph.keys():
                        node_status = 0
                        is_member = yield from certifier['identity'].is_member(self.community)
                        if certifier['identity'].pubkey == identity_account.pubkey:
                            node_status += NODE_STATUS_HIGHLIGHTED
                        if is_member is False:
                            node_status += NODE_STATUS_OUT
                        self._graph[certifier['identity'].pubkey] = {
                            'id': certifier['identity'].pubkey,
                            'arcs': list(),
                            'text': certifier['identity'].uid,
                            'tooltip': certifier['identity'].pubkey,
                            'status': node_status,
                            'connected': [identity.pubkey]
                        }

                    # keep only the latest certification
                    if self._graph[certifier['identity'].pubkey]['arcs']:
                        if certifier['cert_time'] < self._graph[certifier['identity'].pubkey]['arcs'][0]['cert_time']:
                            continue
                    # display validity status
                    if (time.time() - certifier['cert_time']) > self.ARC_STATUS_STRONG_time:
                        arc_status = ARC_STATUS_WEAK
                    else:
                        arc_status = ARC_STATUS_STRONG

                    arc = {
                        'id': identity.pubkey,
                        'status': arc_status,
                        'tooltip': QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(certifier['cert_time'] + self.signature_validity).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        ),
                        'cert_time': certifier['cert_time']
                    }

                    current_block_number = self.community.network.current_blockid.number
                    if current_block_number and certifier['block_number']:
                        current_validations = current_block_number - certifier['block_number']
                    else:
                        current_validations = 0
                    members_pubkeys = yield from self.community.members_pubkeys()
                    max_validation = self.community.network.fork_window(members_pubkeys) + 1

                    # Current validation can be negative if self.community.network.current_blockid.number
                    # is not refreshed yet
                    if max_validation > current_validations >= 0:
                        if self.app.preferences['expert_mode']:
                            arc['validation_text'] = "{0}/{1}".format(current_validations,
                                                                      max_validation)
                        else:
                            validation = current_validations / max_validation * 100
                            arc['validation_text'] = "{0} %".format(QLocale().toString(float(validation), 'f', 0))
                    else:
                        arc['validation_text'] = None

                    #  add arc to certifier
                    self._graph[certifier['identity'].pubkey]['arcs'].append(arc)
                    # if certifier node not in identity nodes
                    if certifier['identity'].pubkey not in tuple(self._graph[identity.pubkey]['connected']):
                        # add certifier node to identity node
                        self._graph[identity.pubkey]['connected'].append(certifier['identity'].pubkey)
            except NoPeerAvailable as e:
                logging.debug(str(e))

    @asyncio.coroutine
    def add_certified_list(self, certified_list, identity, identity_account):
        """
        Add list of certified from api to graph
        :param list certified_list: List of certified from api
        :param identity identity:   identity instance which is certifier
        :param identity identity_account:   Account identity instance
        :return:
        """

        if self.community:
            try:
                yield from self.refresh_signature_validity()
                # add certified by uid
                for certified in tuple(certified_list):
                    # add only valid certification...
                    if (time.time() - certified['cert_time']) > self.signature_validity:
                        continue
                    if certified['identity'].pubkey not in self._graph.keys():
                        node_status = 0
                        is_member = yield from certified['identity'].is_member(self.community)
                        if certified['identity'].pubkey == identity_account.pubkey:
                            node_status += NODE_STATUS_HIGHLIGHTED
                        if is_member is False:
                            node_status += NODE_STATUS_OUT
                        self._graph[certified['identity'].pubkey] = {
                            'id': certified['identity'].pubkey,
                            'arcs': list(),
                            'text': certified['identity'].uid,
                            'tooltip': certified['identity'].pubkey,
                            'status': node_status,
                            'connected': [identity.pubkey]
                        }
                    # display validity status
                    if (time.time() - certified['cert_time']) > self.ARC_STATUS_STRONG_time:
                        arc_status = ARC_STATUS_WEAK
                    else:
                        arc_status = ARC_STATUS_STRONG
                    arc = {
                        'id': certified['identity'].pubkey,
                        'status': arc_status,
                        'tooltip': QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(certified['cert_time'] + self.signature_validity).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        ),
                        'cert_time': certified['cert_time']
                    }

                    current_block_number = self.community.network.current_blockid.number
                    if current_block_number and certified['block_number']:
                        current_validations = current_block_number - certified['block_number']
                    else:
                        current_validations = 0
                    members_pubkeys = yield from self.community.members_pubkeys()
                    max_validations = self.community.network.fork_window(members_pubkeys) + 1

                    if max_validations > current_validations > 0:
                        if self.app.preferences['expert_mode']:
                            arc['validation_text'] = "{0}/{1}".format(current_validations,
                                                                      max_validations)
                        else:
                            validation = current_validations / max_validations * 100
                            validation = 100 if validation > 100 else validation
                            arc['validation_text'] = "{0} %".format(QLocale().toString(float(validation), 'f', 0))
                    else:
                        arc['validation_text'] = None

                    # replace old arc if this one is more recent
                    new_arc = True
                    index = 0
                    for a in self._graph[identity.pubkey]['arcs']:
                        # if same arc already exists...
                        if a['id'] == arc['id']:
                            # if arc more recent, dont keep old one...
                            if arc['cert_time'] >= a['cert_time']:
                                self._graph[identity.pubkey]['arcs'][index] = arc
                            new_arc = False
                        index += 1

                    #  if arc not in graph...
                    if new_arc:
                        # add arc in graph
                        self._graph[identity.pubkey]['arcs'].append(arc)
                    # if certified node not in identity nodes
                    if certified['identity'].pubkey not in tuple(self._graph[identity.pubkey]['connected']):
                        # add certified node to identity node
                        self._graph[identity.pubkey]['connected'].append(certified['identity'].pubkey)
            except NoPeerAvailable as e:
                logging.debug(str(e))

    def add_identity(self, identity, status=None, arcs=None, connected=None):
        """
        Add identity as a new node in graph
        :param identity identity: identity instance
        :param int status:  Optional, default=None, Node status (see cutecoin.gui.views.wot)
        :param list arcs:  Optional, default=None, List of arcs (certified by identity)
        :param list connected:  Optional, default=None, Public key list of the connected nodes around the identity
        :return:
        """
        # functions keywords args are persistent... Need to reset it with None trick
        status = status or (0 and (status is None))
        arcs = arcs or (list() and (arcs is None))
        connected = connected or (list() and (connected is None))
        self._graph[identity.pubkey] = {
            'id': identity.pubkey,
            'arcs': arcs,
            'text': identity.uid,
            'tooltip': identity.pubkey,
            'status': status,
            'connected': connected
        }
