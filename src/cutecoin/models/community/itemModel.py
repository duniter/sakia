'''
Created on 5 févr. 2014

@author: inso
'''

class CommunityItemModel(object):
    def __init__(self, community, communitiesItem=None):
        self.communitiesItem = communitiesItem
        self.communityText = community.name()
        self.mainNodeItems = []

    def appendChild(self, item):
        self.mainNodeItems.append(item)

    def child(self, row):
        return self.mainNodeItems[row]

    def childCount(self):
        return len(self.mainNodeItems)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.communityText
        except IndexError:
            return None

    def parent(self):
        return self.communitiesItem

    def row(self):
        if self.communitiesItem:
            return self.communitiesItem.communityItems.index(self)

        return 0
