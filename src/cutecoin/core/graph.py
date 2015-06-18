import logging
import time
import datetime
from PyQt5.QtCore import QLocale, QDateTime
from ..core.registry import Identity
from cutecoin.gui.views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_OUT, ARC_STATUS_STRONG, ARC_STATUS_WEAK


class Graph(object):
    def __init__(self, community, graph=None):
        """
        Init Graph instance
        :param cutecoin.core.community.Community community:
        :return:
        """

        self.community = community
        self.signature_validity = self.community.parameters['sigValidity']
        #  arc considered strong during 75% of signature validity time
        self.ARC_STATUS_STRONG_time = int(self.signature_validity * 0.75)
        # graph empty if None parameter
        self._graph = graph or (dict() and (graph is None))

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

    def get_shortest_path_between_members(self, from_person, to_person):
        """
        Return path list of nodes from from_person to to_person
        :param Person from_person:
        :param Person to_person:
        :return:
        """
        path = list()

        logging.debug("path between %s to %s..." % (from_person.uid, to_person.uid))
        if from_person.pubkey not in self._graph.keys():
            self.add_person(from_person)
            certifier_list = from_person.certifiers_of(self.community)
            self.add_certifier_list(certifier_list, from_person, to_person)
            certified_list = from_person.certified_by(self.community)
            self.add_certified_list(certified_list, from_person, to_person)

        if to_person.pubkey not in self._graph.keys():
            # recursively feed graph searching for account node...
            self.explore_to_find_member(to_person, self._graph[from_person.pubkey]['connected'], list())
        if len(self._graph[from_person.pubkey]['connected']) > 0:
            # calculate path of nodes between person and to_person
            path = self.find_shortest_path(self._graph[from_person.pubkey], self._graph[to_person.pubkey])

        if path:
            logging.debug([node['text'] for node in path])
        else:
            logging.debug('no wot path')

        return path

    def explore_to_find_member(self, person, connected=None, done=None):
        """
        Scan graph recursively to find person
        :param Person person:   Person instance to find
        :param list connected:  Optional, default=None, Pubkey list of the connected nodes
        around the current scanned node
        :param list done:       Optional, default=None, List of node already scanned
        :return:
        """
        # functions keywords args are persistent... Need to reset it with None trick
        connected = connected or (list() and (connected is None))
        done = done or (list() and (done is None))
        logging.debug("search %s in " % person.uid)
        logging.debug([self._graph[pubkey]['text'] for pubkey in connected])
        # for each pubkey connected...
        for pubkey in tuple(connected):
            # capture node connected
            node = self._graph[pubkey]
            if node['id'] in tuple(done):
                continue
            person_selected = Person.from_metadata(node)
            certifier_list = person_selected.certifiers_of(self.community)
            self.add_certifier_list(certifier_list, person_selected, person)
            if person.pubkey in tuple(self._graph.keys()):
                return False
            certified_list = person_selected.certified_by(self.community)
            self.add_certified_list(certified_list, person_selected, person)
            if person.pubkey in tuple(self._graph.keys()):
                return False
            if node['id'] not in tuple(done):
                done.append(node['id'])
            if len(done) >= len(self._graph):
                return True
            result = self.explore_to_find_member(person, self._graph[person_selected.pubkey]['connected'], done)
            if not result:
                return False

        return True

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
                newpath = self.find_shortest_path(node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    def add_certifier_list(self, certifier_list, person, person_account):
        """
        Add list of certifiers to graph
        :param list certifier_list: List of certifiers from api
        :param Person person:   Person instance which is certified
        :param Person person_account:   Account person instance
        :return:
        """
        #  add certifiers of uid
        for certifier in tuple(certifier_list):
            # add only valid certification...
            if (time.time() - certifier['cert_time']['medianTime']) > self.signature_validity:
                continue
            # new node
            if certifier['pubkey'] not in self._graph.keys():
                node_status = 0
                if certifier['pubkey'] == person_account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certifier['isMember'] is False:
                    node_status += NODE_STATUS_OUT
                self._graph[certifier['pubkey']] = {
                    'id': certifier['pubkey'],
                    'arcs': list(),
                    'text': certifier['uid'],
                    'tooltip': certifier['pubkey'],
                    'status': node_status,
                    'connected': [person.pubkey]
                }

            # keep only the latest certification
            if self._graph[certifier['pubkey']]['arcs']:
                if certifier['cert_time']['medianTime'] < self._graph[certifier['pubkey']]['arcs'][0]['cert_time']:
                    continue
            # display validity status
            if (time.time() - certifier['cert_time']['medianTime']) > self.ARC_STATUS_STRONG_time:
                arc_status = ARC_STATUS_WEAK
            else:
                arc_status = ARC_STATUS_STRONG
            arc = {
                'id': person.pubkey,
                'status': arc_status,
                'tooltip': QLocale.toString(
                    QLocale(),
                    QDateTime.fromTime_t(certifier['cert_time']['medianTime'] + self.signature_validity).date(),
                    QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                ),
                'cert_time': certifier['cert_time']['medianTime']
            }
            #  add arc to certifier
            self._graph[certifier['pubkey']]['arcs'].append(arc)
            # if certifier node not in person nodes
            if certifier['pubkey'] not in tuple(self._graph[person.pubkey]['connected']):
                # add certifier node to person node
                self._graph[person.pubkey]['connected'].append(certifier['pubkey'])

    def add_certified_list(self, certified_list, person, person_account):
        """
        Add list of certified from api to graph
        :param list certified_list: List of certified from api
        :param Person person:   Person instance which is certifier
        :param Person person_account:   Account person instance
        :return:
        """
        # add certified by uid
        for certified in tuple(certified_list):
            # add only valid certification...
            if (time.time() - certified['cert_time']['medianTime']) > self.signature_validity:
                continue
            if certified['pubkey'] not in self._graph.keys():
                node_status = 0
                if certified['pubkey'] == person_account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certified['isMember'] is False:
                    node_status += NODE_STATUS_OUT
                self._graph[certified['pubkey']] = {
                    'id': certified['pubkey'],
                    'arcs': list(),
                    'text': certified['uid'],
                    'tooltip': certified['pubkey'],
                    'status': node_status,
                    'connected': [person.pubkey]
                }
            # display validity status
            if (time.time() - certified['cert_time']['medianTime']) > self.ARC_STATUS_STRONG_time:
                arc_status = ARC_STATUS_WEAK
            else:
                arc_status = ARC_STATUS_STRONG
            arc = {
                'id': certified['pubkey'],
                'status': arc_status,
                'tooltip': QLocale.toString(
                    QLocale(),
                    QDateTime.fromTime_t(certified['cert_time']['medianTime'] + self.signature_validity).date(),
                    QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                ),
                'cert_time': certified['cert_time']['medianTime']
            }

            # replace old arc if this one is more recent
            new_arc = True
            index = 0
            for a in self._graph[person.pubkey]['arcs']:
                # if same arc already exists...
                if a['id'] == arc['id']:
                    # if arc more recent, dont keep old one...
                    if arc['cert_time'] >= a['cert_time']:
                        self._graph[person.pubkey]['arcs'][index] = arc
                    new_arc = False
                index += 1

            #  if arc not in graph...
            if new_arc:
                # add arc in graph
                self._graph[person.pubkey]['arcs'].append(arc)
            # if certified node not in person nodes
            if certified['pubkey'] not in tuple(self._graph[person.pubkey]['connected']):
                # add certified node to person node
                self._graph[person.pubkey]['connected'].append(certified['pubkey'])

    def add_person(self, person, status=None, arcs=None, connected=None):
        """
        Add person as a new node in graph
        :param Person person: Person instance
        :param int status:  Optional, default=None, Node status (see cutecoin.gui.views.wot)
        :param list arcs:  Optional, default=None, List of arcs (certified by person)
        :param list connected:  Optional, default=None, Public key list of the connected nodes around the person
        :return:
        """
        # functions keywords args are persistent... Need to reset it with None trick
        status = status or (0 and (status is None))
        arcs = arcs or (list() and (arcs is None))
        connected = connected or (list() and (connected is None))
        self._graph[person.pubkey] = {
            'id': person.pubkey,
            'arcs': arcs,
            'text': person.uid,
            'tooltip': person.pubkey,
            'status': status,
            'connected': connected
        }
