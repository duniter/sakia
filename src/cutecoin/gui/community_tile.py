"""
@author: inso
"""

import asyncio
import enum

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QLayout
from PyQt5.QtCore import QSize, pyqtSignal
from ucoinpy.documents.block import Block

from ..tools.decorators import asyncify
from ..tools.exceptions import NoPeerAvailable
from cutecoin.gui.widgets.busy import Busy


@enum.unique
class CommunityState(enum.Enum):
    NOT_INIT = 0
    OFFLINE = 1
    READY = 2


class CommunityTile(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent, app, community):
        super().__init__(parent)
        self.app = app
        self.community = community
        self.community.network.nodes_changed.connect(self.handle_nodes_change)
        self.text_label = QLabel()
        self.setLayout(QVBoxLayout())
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.layout().addWidget(self.text_label)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.busy = Busy(self)
        self.busy.hide()
        self._state = CommunityState.NOT_INIT
        self.refresh()

    def sizeHint(self):
        return QSize(250, 250)

    def handle_nodes_change(self):
        if len(self.community.network.online_nodes) > 0:
            if self.community.network.current_blockid.sha_hash == Block.Empty_Hash:
                state = CommunityState.NOT_INIT
            else:
                state = CommunityState.READY
        else:
            state = CommunityState.OFFLINE

        if state != self._state:
            self.refresh()

    @asyncify
    @asyncio.coroutine
    def refresh(self):
        self.busy.show()
        self.setFixedSize(QSize(150, 150))
        try:
            current_block = yield from self.community.get_block()
            members_pubkeys = yield from self.community.members_pubkeys()
            amount = yield from self.app.current_account.amount(self.community)
            localized_amount = yield from self.app.current_account.current_ref(amount,
                                                        self.community, self.app).localized(units=True,
                                            international_system=self.app.preferences['international_system_of_units'])
            if current_block['monetaryMass']:
                localized_monetary_mass = yield from self.app.current_account.current_ref(current_block['monetaryMass'],
                                                        self.community, self.app).localized(units=True,
                                            international_system=self.app.preferences['international_system_of_units'])
            else:
                localized_monetary_mass = ""
            status = self.tr("Member") if self.app.current_account.pubkey in members_pubkeys \
                else self.tr("Non-Member")
            description = """<html>
            <body>
            <p>
            <span style=" font-size:16pt; font-weight:600;">{currency}</span>
            </p>
            <p>{nb_members} {members_label}</p>
            <p><span style=" font-weight:600;">{monetary_mass_label}</span> : {monetary_mass}</p>
            <p><span style=" font-weight:600;">{status_label}</span> : {status}</p>
            <p><span style=" font-weight:600;">{balance_label}</span> : {balance}</p>
            </body>
            </html>""".format(currency=self.community.currency,
                              nb_members=len(members_pubkeys),
                              members_label=self.tr("members"),
                              monetary_mass_label=self.tr("Monetary mass"),
                              monetary_mass=localized_monetary_mass,
                              status_label=self.tr("Status"),
                              status=status,
                              balance_label=self.tr("Balance"),
                              balance=localized_amount)
            self.text_label.setText(description)
            self._state = CommunityState.READY
        except NoPeerAvailable:
            description = """<html>
            <body>
            <p>
            <span style=" font-size:16pt; font-weight:600;">{currency}</span>
            </p>
            <p>{message}</p>
            </body>
            </html>""".format(currency=self.community.currency,
                              message=self.tr("Not connected"))
            self.text_label.setText(description)
            self._state = CommunityState.OFFLINE
        except ValueError as e:
            if '404' in str(e):
                description = """<html>
                <body>
                <p>
                <span style=" font-size:16pt; font-weight:600;">{currency}</span>
                </p>
                <p>{message}</p>
                </body>
                </html>""".format(currency=self.community.currency,
                              message=self.tr("Community not initialized"))
                self.text_label.setText(description)
                self._state = CommunityState.NOT_INIT
            else:
                raise

        self.busy.hide()

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super().mousePressEvent(event)

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet("color: rgb(0, 115, 173);")
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("")
        return super().leaveEvent(event)