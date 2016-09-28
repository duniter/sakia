import attr
from ..entities import Node
from duniterpy.documents import BlockUID, endpoint
import logging


@attr.s
class NodesProcessor:
    _currency = attr.ib(convert=str)
    _repo = attr.ib()  # :type sakia.data.repositories.NodesRepo

    def synced_nodes(self):
        """
        Get nodes which are in the ONLINE state.
        """
        return self._repo.get_all(**{'currency': self._currency, 'state': Node.ONLINE})

    def online_nodes(self):
        """
        Get nodes which are in the ONLINE state.
        """
        return self._repo.get_all(**{'currency': self._currency, 'state': Node.ONLINE}) + \
               self._repo.get_all(**{'currency': self._currency, 'state': Node.DESYNCED})

    def update_node(self, node):
        """
        Update node in the repository.
        First involves basic checks about pubkey and primary key constraints.

        :param sakia.data.entities.Node node: the node to update
        """
        other_node = self._repo.get_one(**{'currency': self._currency, 'pubkey': node.pubkey})
        if other_node:
            self._repo.update(node)
        else:
            self._repo.insert(node)

    def nodes(self):
        """
        Get all knew nodes.
        """
        return self._repo.get_all(**{'currency': self._currency})

    def root_nodes(self):
        """
        Get root nodes.
        """
        return self._repo.get_all(**{'currency': self._currency, 'root': True})

    def current_buid(self):
        """
        Get the latest block considered valid
        It is the most frequent last block of every known nodes
        """
        blocks_uids = [n.current_buid for n in self.synced_nodes()]
        if len(blocks_uids) > 0:
            return blocks_uids[0]
        else:
            return BlockUID.empty()

    def quality(self):
        """
        Get a ratio of the synced nodes vs the rest
        """
        synced = len(self.synced_nodes())
        total = len(self.nodes())
        if total == 0:
            ratio_synced = 0
        else:
            ratio_synced = synced / total
        return ratio_synced

    def update_peer(self, peer):
        """
        Update the peer of a node
        :param peer:
        :return:
        """
        node = self._repo.get_one(**{'pubkey': peer.pubkey, 'currency': self._currency})
        if node.peer_blockstamp < peer.blockUID:
            logging.debug("Update node : {0}".format(peer.pubkey[:5]))
            node.endpoints = tuple(peer.endpoints)
            node.peer_blockstamp = peer.blockUID
            self._repo.update(node)
