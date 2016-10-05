import logging
import time
import networkx
from PyQt5.QtCore import QLocale, QDateTime, QObject
from sakia.errors import NoPeerAvailable
from .constants import EdgeStatus, NodeStatus
from sakia.constants import MAX_CONFIRMATIONS


class BaseGraph(QObject):
    def __init__(self, app, community, nx_graph=None):
        """
        Init Graph instance
        :param sakia.core.app.Application app: Application instance
        :param sakia.core.community.Community community: Community instance
        :param networkx.Graph nx_graph: The networkx graph
        :return:
        """
        super().__init__()
        self.app = app
        self.community = community
        # graph empty if None parameter
        self.nx_graph = nx_graph if nx_graph else networkx.DiGraph()

    async def arc_status(self, cert_time):
        """
        Get arc status of a certification
        :param int cert_time: the timestamp of the certification
        :return: the certification time
        """
        parameters = await self.community.parameters()
        signature_validity = parameters['sigValidity']
        #  arc considered strong during 75% of signature validity time
        arc_strong = int(signature_validity * 0.75)
        # display validity status
        ts = time.time()
        if (time.time() - cert_time) > arc_strong:
            return EdgeStatus.WEAK
        else:
            return EdgeStatus.STRONG

    async def node_status(self, node_identity, account_identity):
        """
        Return the status of the node depending
        :param sakia.core.registry.Identity node_identity: The identity of the node
        :param sakia.core.registry.Identity account_identity: The identity of the account displayed
        :return: HIGHLIGHTED if node_identity is account_identity and OUT if the node_identity is not a member
        :rtype: sakia.core.graph.constants.NodeStatus
        """
        # new node
        node_status = NodeStatus.NEUTRAL
        is_member = await node_identity.is_member(self.community)
        if node_identity.pubkey == account_identity.pubkey:
            node_status += NodeStatus.HIGHLIGHTED
        if is_member is False:
            node_status += NodeStatus.OUT
        return node_status

    def confirmation_text(self, block_number):
        """
        Build confirmation text of an arc
        :param int block_number: the block number of the certification
        :return: the confirmation text
        :rtype: str
        """
        try:
            current_confirmations = self.community.network.confirmations(block_number)

            if MAX_CONFIRMATIONS > current_confirmations:
                if self.app.preferences['expert_mode']:
                    return "{0}/{1}".format(current_confirmations,
                                                              MAX_CONFIRMATIONS)
                else:
                    confirmation = current_confirmations / MAX_CONFIRMATIONS * 100
                    return "{0} %".format(QLocale().toString(float(confirmation), 'f', 0))
        except ValueError:
            pass
        return None

    def is_sentry(self, nb_certs, nb_members):
        """
        Check if it is a sentry or not
        :param int nb_certs: the number of certs
        :param int nb_members: the number of members
        :return: True if a sentry
        """
        Y = {
            10: 2,
            100: 4,
            1000: 6,
            10000: 12,
            100000: 20
        }
        for k in reversed(sorted(Y.keys())):
            if nb_members >= k:
                return nb_certs >= Y[k]
        return False

    async def add_certifier_list(self, certifier_list, identity, account_identity):
        """
        Add list of certifiers to graph
        :param list certifier_list: List of certifiers from api
        :param sakia.core.registry.Identity identity:   identity instance which is certified
        :param sakia.core.registry.Identity account_identity:   Account identity instance
        :return:
        """
        if self.community:
            try:
                #  add certifiers of uid
                for certifier in tuple(certifier_list):
                    node_status = await self.node_status(certifier['identity'], account_identity)
                    metadata = {
                        'text': certifier['identity'].uid,
                        'tooltip': certifier['identity'].pubkey,
                        'status': node_status
                    }
                    self.nx_graph.add_node(certifier['identity'].pubkey, attr_dict=metadata)

                    arc_status = await self.arc_status(certifier['cert_time'])
                    sig_validity = (await self.community.parameters())['sigValidity']
                    arc = {
                        'status': arc_status,
                        'tooltip': QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(certifier['cert_time'] + sig_validity).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        ),
                        'cert_time': certifier['cert_time'],
                        'confirmation_text': self.confirmation_text(certifier['block_number'])
                    }

                    self.nx_graph.add_edge(certifier['identity'].pubkey, identity.pubkey, attr_dict=arc, weight=len(certifier_list))
            except NoPeerAvailable as e:
                logging.debug(str(e))

    async def add_certified_list(self, certified_list, identity, account_identity):
        """
        Add list of certified from api to graph
        :param list certified_list: List of certified from api
        :param identity identity:   identity instance which is certifier
        :param identity account_identity:   Account identity instance
        :return:
        """

        if self.community:
            try:
                # add certified by uid
                for certified in tuple(certified_list):
                    node_status = await self.node_status(certified['identity'], account_identity)
                    metadata = {
                        'text': certified['identity'].uid,
                        'tooltip': certified['identity'].pubkey,
                        'status': node_status
                    }
                    self.nx_graph.add_node(certified['identity'].pubkey, attr_dict=metadata)

                    arc_status = await self.arc_status(certified['cert_time'])
                    sig_validity = (await self.community.parameters())['sigValidity']
                    arc = {
                        'status': arc_status,
                        'tooltip': QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(certified['cert_time'] + sig_validity).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        ),
                        'cert_time': certified['cert_time'],
                        'confirmation_text': self.confirmation_text(certified['block_number'])
                    }

                    self.nx_graph.add_edge(identity.pubkey, certified['identity'].pubkey, attr_dict=arc,
                                           weight=len(certified_list))

            except NoPeerAvailable as e:
                logging.debug(str(e))

    def add_identity(self, identity, status):
        """
        Add identity as a new node in graph
        :param identity identity: identity instance
        :param int status:  Optional, default=None, Node status (see sakia.gui.views.wot)
        :param list edges:  Optional, default=None, List of edges (certified by identity)
        :param list connected:  Optional, default=None, Public key list of the connected nodes around the identity
        """
        metadata = {
            'text': identity.uid,
            'tooltip': identity.pubkey,
            'status': status
        }
        self.nx_graph.add_node(identity.pubkey, attr_dict=metadata)
