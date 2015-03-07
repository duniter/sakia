import logging
import copy
import time
import datetime
from cutecoin.core.person import Person
from cutecoin.gui.views.wot import NODE_STATUS_HIGHLIGHTED, NODE_STATUS_OUT, ARC_STATUS_STRONG, ARC_STATUS_WEAK


class Graph(dict):

    def __init__(self, community):
        """
        Init Graph instance
        :param cutecoin.core.community.Community community:
        :return:
        """
        self.community = community
        self.signature_validity = self.community.get_parameters()['sigValidity']
        # arc considered strong during 75% of signature validity time
        self.ARC_STATUS_STRONG_time = int(self.signature_validity * 0.75)

    def get_shortest_path_between_members(self, from_person, to_person):
        """
        Return path list of nodes from from_person to to_person
        :param Person from_person:
        :param Person to_person:
        :return:
        """
        path = list()
        graph_tmp = copy.deepcopy(self)

        logging.debug("path between %s to %s..." % (from_person.name, to_person.name))
        if from_person.pubkey not in graph_tmp.keys():
            graph_tmp.add_person(from_person)
            certifier_list = from_person.certifiers_of(self.community)
            graph_tmp.add_certifier_list(certifier_list, from_person, to_person)
            certified_list = from_person.certified_by(self.community)
            graph_tmp.add_certified_list(certified_list, from_person, to_person)

        if to_person.pubkey not in graph_tmp.keys():
            # recursively feed graph searching for account node...
            graph_tmp.explore_to_find_member(to_person, graph_tmp[from_person.pubkey]['nodes'], list())
        if len(graph_tmp[from_person.pubkey]['nodes']) > 0:
            # calculate path of nodes between person and to_person
            path = graph_tmp.find_shortest_path(graph_tmp[from_person.pubkey], graph_tmp[to_person.pubkey])

        if path:
            logging.debug([node['text'] for node in path])
        else:
            logging.debug('no wot path')

        return path

    def explore_to_find_member(self, person, nodes=None, done=None):
        """
        Scan graph recursively to find person
        :param Person person:   Person instance to find
        :param list nodes:      Optional, default=None, List of nodes around the person
        :param list done:       Optional, default=None, List of node already scanned
        :return:
        """
        # functions keywords args are persistent... Need to reset it with None trick
        nodes = nodes or (list() and (nodes is None))
        done = done or (list() and (done is None))
        logging.debug("search %s in " % person.name)
        logging.debug([node['text'] for node in nodes])
        for node in tuple(nodes):
            if node['id'] in tuple(done):
                continue
            person_selected = Person(node['text'], node['id'])
            certifier_list = person_selected.certifiers_of(self.community)
            self.add_certifier_list(certifier_list, person_selected, person)
            if person.pubkey in tuple(self.keys()):
                return False
            certified_list = person_selected.certified_by(self.community)
            self.add_certified_list(certified_list, person_selected, person)
            if person.pubkey in tuple(self.keys()):
                return False
            if node['id'] not in tuple(done):
                done.append(node['id'])
            if len(done) >= len(self):
                return True
            result = self.explore_to_find_member(person, self[person_selected.pubkey]['nodes'], done)
            if not result:
                return False

        return True

    def find_shortest_path(self, start, end, path=list()):
        """
        Find recursively the shortest path between two nodes
        :param dict start:
        :param dict end:
        :param list path:
        :return:
        """
        path = path + [start]
        if start['id'] == end['id']:
            return path
        if start['id'] not in self.keys():
            return None
        shortest = None
        for node in tuple(self[start['id']]['nodes']):
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
        # add certifiers of uid
        for certifier in tuple(certifier_list):
            # add only valid certification...
            if (time.time() - certifier['cert_time']['medianTime']) > self.signature_validity:
                continue
            # new node
            if certifier['pubkey'] not in self.keys():
                node_status = 0
                if certifier['pubkey'] == person_account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certifier['isMember'] is False:
                    node_status += NODE_STATUS_OUT
                self[certifier['pubkey']] = {
                    'id': certifier['pubkey'],
                    'arcs': list(),
                    'text': certifier['uid'],
                    'tooltip': certifier['pubkey'],
                    'status': node_status,
                    'nodes': [self[person.pubkey]]
                }

            # keep only the latest certification
            if self[certifier['pubkey']]['arcs']:
                if certifier['cert_time']['medianTime'] < self[certifier['pubkey']]['arcs'][0]['cert_time']:
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
            self[certifier['pubkey']]['arcs'].append(arc)
            # if certifier node not in person nodes
            if self[certifier['pubkey']] not in tuple(self[person.pubkey]['nodes']):
                # add certifier node to person node
                self[person.pubkey]['nodes'].append(self[certifier['pubkey']])

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
            if certified['pubkey'] not in self.keys():
                node_status = 0
                if certified['pubkey'] == person_account.pubkey:
                    node_status += NODE_STATUS_HIGHLIGHTED
                if certified['isMember'] is False:
                    node_status += NODE_STATUS_OUT
                self[certified['pubkey']] = {
                    'id': certified['pubkey'],
                    'arcs': list(),
                    'text': certified['uid'],
                    'tooltip': certified['pubkey'],
                    'status': node_status,
                    'nodes': [self[person.pubkey]]
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
            for a in self[person.pubkey]['arcs']:
                # if same arc already exists...
                if a['id'] == arc['id']:
                    # if arc more recent, dont keep old one...
                    if arc['cert_time'] >= a['cert_time']:
                        self[person.pubkey]['arcs'][index] = arc
                    new_arc = False
                index += 1

            # if arc not in graph...
            if new_arc:
                # add arc in graph
                self[person.pubkey]['arcs'].append(arc)
            # if certified node not in person nodes
            if self[certified['pubkey']] not in tuple(self[person.pubkey]['nodes']):
                # add certified node to person node
                self[person.pubkey]['nodes'].append(self[certified['pubkey']])

    def add_person(self, person, status=0, arcs=None, nodes=None):
        """
        Add person as a new node in graph
        :param Person person: Person instance
        :param int status:  Node status (see cutecoin.gui.views.wot)
        :param list arcs:  List of arcs (certified by person)
        :param list nodes:  List of nodes around person
        :return:
        """
        # functions keywords args are persistent... Need to reset it with None trick
        arcs = arcs or (list() and (arcs is None))
        nodes = nodes or (list() and (nodes is None))
        self[person.pubkey] = {
            'id': person.pubkey,
            'arcs': arcs,
            'text': person.name,
            'tooltip':  person.pubkey,
            'status': status,
            'nodes': nodes
        }
