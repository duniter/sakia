'''
Created on 5 févr. 2014

@author: inso
'''


class CommunitiesItemModel(object):

    def __init__(self, account):
        self.communities_text = account.key
        self.community_items = []

    def appendChild(self, community_item):
        self.community_items.append(community_item)

    def child(self, row):
        return self.communityItems[row]

    def childCount(self):
        return len(self.community_items)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.communities_text
        except IndexError:
            return None

    def parent(self):
        return None

    def row(self):
        return 0
