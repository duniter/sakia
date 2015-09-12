import datetime
import asyncio

from PyQt5.QtWidgets import QDialog

from ..core.graph import Graph
from ..tools.decorators import asyncify
from ..gen_resources.member_uic import Ui_DialogMember
from ..tools.exceptions import MembershipNotFoundError


class MemberDialog(QDialog, Ui_DialogMember):
    """
    classdocs
    """

    def __init__(self, app, account, community, identity):
        """
        Init MemberDialog

        :param cutecoin.core.app.Application app:   Application instance
        :param cutecoin.core.account.Account account:   Account instance
        :param cutecoin.core.community.Community community: Community instance
        :param cutecoin.core.registry.identity.Identity identity: Identity instance
        :return:
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.community = community
        self.account = account
        self.identity = identity
        self.label_uid.setText(identity.uid)
        self.refresh()

    @asyncify
    @asyncio.coroutine
    def refresh(self):

        try:
            join_date = yield from self.identity.get_join_date(self.community)
        except MembershipNotFoundError:
            join_date = None

        if join_date is None:
            join_date = self.tr('not a member')
        else:
            join_date = datetime.datetime.fromtimestamp(join_date).strftime("%d/%m/%Y %I:%M")

        # calculate path to account member
        graph = Graph(self.app, self.community)
        path = None
        # if selected member is not the account member...
        if self.identity.pubkey != self.account.pubkey:
            # add path from selected member to account member
            account_identity = yield from self.account.identity(self.community)
            path = yield from graph.get_shortest_path_between_members(self.identity,
                                                                      account_identity)

        text = self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
            """).format(
            self.tr('Public key'),
            self.identity.pubkey,
            self.tr('Join date'),
            join_date
        )

        if path:
            distance = len(path) - 1
            text += self.tr(
                """<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>"""
                    .format(self.tr('Distance'), distance))
            if distance > 1:
                index = 0
                for node in path:
                    if index == 0:
                        text += self.tr("""<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>""").format(
                            self.tr('Path'), node['text'])
                    else:
                        text += self.tr("""<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>""").format('',
                                                                                                                   node[
                                                                                                                       'text'])
                    if index == distance and node['id'] != self.account.pubkey:
                        text += self.tr("""<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>""").format('',
                                                                                                                   self.account.name)
                    index += 1
        # close html text
        text += "</table>"

        # set text in label
        self.label_properties.setText(text)
