"""
Created on 5 fevr. 2014

@author: inso
"""


class CommunityItemModel(object):

    def __init__(self, community, communities_item=None):
        self.communities_item = communities_item
        self.community_text = community.name
        self.main_node_items = []

    def appendChild(self, item):
        self.main_node_items.append(item)

    def child(self, row):
        return self.main_node_items[row]

    def childCount(self):
        return len(self.main_node_items)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.community_text
        except IndexError:
            return None

    def parent(self):
        return self.communities_item

    def row(self):
        if self.communities_item:
            return self.communities_item.index(self)

        return 0
