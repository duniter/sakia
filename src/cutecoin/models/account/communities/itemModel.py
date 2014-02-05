'''
Created on 5 févr. 2014

@author: inso
'''

class CommunitiesItemModel(object):
    def __init__(self, account):
        self.communitiesText = account.pgpKey
        self.communityItems = []

    def appendChild(self, communityItem):
        self.communityItems.append(communityItem)

    def child(self, row):
        return self.communityItems[row]

    def childCount(self):
        return len(self.communityItems)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.communitiesText
        except IndexError:
            return None

    def parent(self):
        return None

    def row(self):
        return 0