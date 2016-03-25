import datetime

from PyQt5.QtCore import QObject, QEvent, QLocale, QDateTime
from PyQt5.QtWidgets import QDialog, QWidget

from ..core.graph import WoTGraph
from .widgets.busy import Busy
from ..tools.decorators import asyncify
from ..gen_resources.member_uic import Ui_MemberView
from ..tools.exceptions import MembershipNotFoundError, LookupFailureError, NoPeerAvailable


class MemberDialog(QObject):
    """
    A widget showing informations about a member
    """

    def __init__(self, app, account, community, identity, widget, ui):
        """
        Init MemberDialog

        :param sakia.core.app.Application app:   Application instance
        :param sakia.core.account.Account account:   Account instance
        :param sakia.core.community.Community community: Community instance
        :param sakia.core.registry.identity.Identity identity: Identity instance
        :param PyQt5.QtWidget widget: The class of the widget
        :param sakia.gen_resources.member_uic.Ui_DialogMember ui: the class of the ui applyed to the widget
        :return:
        """
        super().__init__()
        self.widget = widget
        self.ui = ui
        self.ui.setupUi(self.widget)
        self.ui.busy = Busy(self.widget)
        self.widget.installEventFilter(self)
        self.app = app
        self.community = community
        self.account = account
        self.identity = identity

    @classmethod
    def open_dialog(cls, app, account, community, identity):
        dialog = cls(app, account, community, identity, QDialog(), Ui_MemberView())
        dialog.refresh()
        dialog.refresh_path()
        dialog.exec()

    @classmethod
    def as_widget(cls, parent_widget, app, account, community, identity):
        return cls(app, account, community, identity, QWidget(parent_widget), Ui_MemberView())

    def change_community(self, community):
        """
        Change current community
        :param sakia.core.Community community: the new community
        """
        self.community = community
        self.refresh()

    @asyncify
    async def refresh(self):
        if self.identity:
            self.ui.busy.show()
            self.ui.label_uid.setText(self.identity.uid)
            self.ui.label_properties.setText("")
            try:

                identity_selfcert = await self.identity.selfcert(self.community)
                publish_time = await self.community.time(identity_selfcert.timestamp.number)

                join_date = await self.identity.get_join_date(self.community)
                if join_date is None:
                    join_date = self.tr('not a member')
                else:
                    join_date = datetime.datetime.fromtimestamp(join_date).strftime("%d/%m/%Y %I:%M")

            except MembershipNotFoundError:
                join_date = "###"
            except (LookupFailureError, NoPeerAvailable):
                publish_time = None
                join_date = "###"

            if publish_time:
                uid_publish_date = QLocale.toString(
                        QLocale(),
                        QDateTime.fromTime_t(publish_time),
                        QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                    )
            else:
                uid_publish_date = "###"

            text = self.tr("""
                <table cellpadding="5">
                <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
                <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
                """).format(
                self.tr('Public key'),
                self.identity.pubkey,
                self.tr('UID Published on'),
                uid_publish_date,
                self.tr('Join date'),
                join_date
            )
            # close html text
            text += "</table>"

            # set text in label
            self.ui.label_properties.setText(text)
            self.ui.busy.hide()

    @asyncify
    async def refresh_path(self):
        text = ""
        self.ui.label_path.setText("")
        # calculate path to account member
        graph = WoTGraph(self.app, self.community)
        path = None
        # if selected member is not the account member...
        if self.identity.pubkey != self.account.pubkey:
            # add path from selected member to account member
            account_identity = await self.account.identity(self.community)
            path = await graph.get_shortest_path_to_identity(self.identity,
                                                            account_identity)
            nodes = graph.nx_graph.nodes(data=True)

        if path:
            distance = len(path) - 1
            text += self.tr(
                """<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>"""
                    .format(self.tr('Distance'), distance))
            if distance > 1:
                index = 0
                for node_id in path:
                    node = [n for n in nodes if n[0] == node_id][0]
                    if index == 0:
                        text += self.tr("""<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>""")\
                            .format(self.tr('Path'), node[1]['text'])
                    else:
                        text += self.tr("""<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>""")\
                            .format('', node[1]['text'] )
                    if index == distance and node_id != self.account.pubkey:
                        text += self.tr("""<tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>""")\
                            .format('', self.account.name)
                    index += 1
        self.ui.label_path.setText(text)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Resize:
            self.ui.busy.resize(event.size())
            self.widget.resizeEvent(event)
        return self.widget.eventFilter(source, event)

    def exec(self):
        self.widget.exec()
