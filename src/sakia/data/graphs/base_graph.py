import logging
import time
import networkx
from sakia.data.processors import ConnectionsProcessor
from PyQt5.QtCore import QLocale, QDateTime, QObject, QT_TRANSLATE_NOOP
from sakia.errors import NoPeerAvailable
from .constants import EdgeStatus, NodeStatus
from sakia.constants import MAX_CONFIRMATIONS
import asyncio


def sentry_display(identity):
    sentry_text = ""
    sentry_symbol = ""
    if identity.sentry:
        sentry_symbol = "✴ "
        sentry_text = QT_TRANSLATE_NOOP("BaseGraph", "(sentry)") + " "
    return sentry_symbol, sentry_text


class BaseGraph(QObject):
    def __init__(self, app, blockchain_service, identities_service, nx_graph):
        """
        Init Graph instance
        :param sakia.app.Application app: Application instance
        :param sakia.services.BlockchainService blockchain_service: Blockchain service instance
        :param sakia.services.IdentitiesService identities_service: Identities service instance
        :param networkx.Graph nx_graph: The networkx graph
        :return:
        """
        super().__init__()
        self.app = app
        self.identities_service = identities_service
        self.blockchain_service = blockchain_service
        self._connections_processor = ConnectionsProcessor.instanciate(app)
        # graph empty if None parameter
        self.nx_graph = nx_graph if nx_graph else networkx.DiGraph()

    def arc_status(self, cert_time):
        """
        Get arc status of a certification
        :param int cert_time: the timestamp of the certification
        :return: the certification time
        """
        parameters = self.blockchain_service.parameters()
        #  arc considered strong during 75% of signature validity time
        arc_strong = int(parameters.sig_validity * 0.75)
        # display validity status
        if (time.time() - cert_time) > arc_strong:
            return EdgeStatus.WEAK
        else:
            return EdgeStatus.STRONG

    def node_status(self, node_identity):
        """
        Return the status of the node depending
        :param sakia.core.registry.Identity node_identity: The identity of the node
        :return: HIGHLIGHTED if node_identity is account_identity and OUT if the node_identity is not a member
        :rtype: sakia.core.graph.constants.NodeStatus
        """
        # new node
        node_status = NodeStatus.NEUTRAL
        if node_identity.pubkey in self._connections_processor.pubkeys():
            node_status += NodeStatus.HIGHLIGHTED
        if node_identity.member is False:
            node_status += NodeStatus.OUT
        return node_status

    def confirmation_text(self, block_number):
        """
        Build confirmation text of an arc
        :param int block_number: the block number of the certification
        :return: the confirmation text
        :rtype: str
        """
        if block_number >= 0:
            current_confirmations = min(max(self.blockchain_service.current_buid().number - block_number, 0), 6)
        else:
            current_confirmations = 0

        if MAX_CONFIRMATIONS > current_confirmations:
            if self.app.parameters.expert_mode:
                return "{0}/{1}".format(current_confirmations, MAX_CONFIRMATIONS)
            else:
                confirmation = current_confirmations / MAX_CONFIRMATIONS * 100
                return "{0} %".format(QLocale().toString(float(confirmation), 'f', 0))
        return None

    def add_certifier_node(self, certifier, identity, certification, node_status):
        sentry_symbol, sentry_text = sentry_display(certifier)
        name_text = certifier.uid if certifier.uid else certifier.pubkey[:12]
        metadata = {
            'text': sentry_symbol + name_text,
            'tooltip': sentry_text + certifier.pubkey,
            'identity': certifier,
            'status': node_status
        }
        self.nx_graph.add_node(certifier.pubkey, attr_dict=metadata)

        arc_status = self.arc_status(certification.timestamp)
        sig_validity = self.blockchain_service.parameters().sig_validity
        expiration = self.blockchain_service.adjusted_ts(certification.timestamp + sig_validity)
        arc = {
            'status': arc_status,
            'tooltip': QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(expiration).date(),
                QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
            ) + " BAT",
            'cert_time': certification.timestamp,
            'confirmation_text': self.confirmation_text(certification.written_on)
        }
        self.nx_graph.add_edge(certifier.pubkey, identity.pubkey, attr_dict=arc)

    def add_certified_node(self, identity, certified, certification, node_status):
        sentry_symbol, sentry_text = sentry_display(certified)
        name_text = certified.uid if certified.uid else certified.pubkey[:12]
        metadata = {
            'text': sentry_symbol + name_text,
            'tooltip': sentry_text + certified.pubkey,
            'identity': certified,
            'status': node_status
        }
        self.nx_graph.add_node(certified.pubkey, attr_dict=metadata)

        arc_status = self.arc_status(certification.timestamp)
        sig_validity = self.blockchain_service.parameters().sig_validity
        expiration = self.blockchain_service.adjusted_ts(certification.timestamp + sig_validity)
        arc = {
            'status': arc_status,
            'tooltip': QLocale.toString(
                QLocale(),
                QDateTime.fromTime_t(expiration).date(),
                QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
            ) + " BAT",
            'cert_time': certification.timestamp,
            'confirmation_text': self.confirmation_text(certification.written_on)
        }

        self.nx_graph.add_edge(identity.pubkey, certified.pubkey, attr_dict=arc)

    def add_certifier_list(self, certifier_list, identity):
        """
        Add list of certifiers to graph
        :param List[sakia.data.entities.Certification] certifier_list: List of certified from api
        :param sakia.data.entities.Identity identity:   identity instance which is certified
        :return:
        """
        try:
            #  add certifiers of uid
            for certification in certifier_list:
                certifier = self.identities_service.get_identity(certification.certifier)
                if not certifier:
                    certifier = certifier_list[certification]
                node_status = self.node_status(certifier)
                self.add_certifier_node(certifier, identity, certification, node_status)
        except NoPeerAvailable as e:
            logging.debug(str(e))

    def add_certified_list(self, certified_list, identity):
        """
        Add list of certified from api to graph
        :param List[sakia.data.entities.Certification] certified_list: List of certified from api
        :param identity identity:   identity instance which is certifier
        :return:
        """
        try:
            # add certified by uid
            for certification in tuple(certified_list):
                certified = self.identities_service.get_identity(certification.certified)
                if not certified:
                    certified = certified_list[certification]
                node_status = self.node_status(certified)
                self.add_certified_node(identity, certified, certification, node_status)

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
        sentry_symbol, sentry_text = sentry_display(identity)
        name_text = identity.uid
        metadata = {
            'text': sentry_symbol + name_text,
            'tooltip': sentry_text + identity.pubkey,
            'status': status,
            'identity': identity
        }
        self.nx_graph.add_node(identity.pubkey, attr_dict=metadata)
