"""
@author: inso
"""

import enum

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QLayout
from PyQt5.QtCore import QSize, pyqtSignal, QTime
from duniterpy.documents.block import Block
from duniterpy.api import errors

from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ..tools.exceptions import NoPeerAvailable
from .widgets.busy import Busy


@enum.unique
class CommunityState(enum.Enum):
    NOT_INIT = 0
    OFFLINE = 1
    READY = 2


class CommunityTile(QFrame):
    clicked = pyqtSignal()
    _hover_stylesheet = """QFrame#CommunityTile {
border-radius: 5px;
background-color: palette(midlight);
}
"""
    _pressed_stylesheet = """QFrame#CommunityTile {
border-radius: 5px;
background-color: palette(dark);
}
"""
    _standard_stylesheet = """QFrame#CommunityTile {
border-radius: 5px;
background-color: palette(base);
}
"""

    def __init__(self, parent, app, community):
        super().__init__(parent)
        self.setObjectName("CommunityTile")
        self.app = app
        self.community = community
        self.community.network.nodes_changed.connect(self.handle_nodes_change)
        self.text_label = QLabel()
        self.setLayout(QVBoxLayout())
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.layout().addWidget(self.text_label)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(CommunityTile._standard_stylesheet)
        self.busy = Busy(self)
        self.busy.hide()
        self._state = CommunityState.NOT_INIT
        self.refresh()

    def sizeHint(self):
        return QSize(250, 250)

    def handle_nodes_change(self):
        if len(self.community.network.online_nodes) > 0:
            if self.community.network.current_blockUID.sha_hash == Block.Empty_Hash:
                state = CommunityState.NOT_INIT
            else:
                state = CommunityState.READY
        else:
            state = CommunityState.OFFLINE

        if state != self._state:
            self.refresh()

    def cancel_refresh(self):
        cancel_once_task(self, self.refresh)

    @once_at_a_time
    @asyncify
    async def refresh(self):
        self.busy.show()
        self.setFixedSize(QSize(150, 150))
        try:
            current_block = await self.community.get_block()
            members_pubkeys = await self.community.members_pubkeys()
            amount = await self.app.current_account.amount(self.community)
            localized_amount = await self.app.current_account.current_ref.instance(amount,
                                                        self.community, self.app).localized(units=True,
                                            international_system=self.app.preferences['international_system_of_units'])
            if current_block['monetaryMass']:
                localized_monetary_mass = await self.app.current_account.current_ref.instance(current_block['monetaryMass'],
                                                        self.community, self.app).diff_localized(units=True,
                                            international_system=self.app.preferences['international_system_of_units'])
            else:
                localized_monetary_mass = ""
            status = self.app.current_account.pubkey in members_pubkeys
            account_identity = await self.app.current_account.identity(self.community)

            mstime_remaining_text = self.tr("Expired or never published")
            outdistanced_text = self.tr("Outdistanced")

            requirements = await account_identity.requirements(self.community)
            mstime_remaining = 0
            nb_certs = 0
            if requirements:
                mstime_remaining = requirements['membershipExpiresIn']
                nb_certs = len(requirements['certifications'])
                if not requirements['outdistanced']:
                    outdistanced_text = self.tr("In WoT range")

            if mstime_remaining > 0:
                days, remainder = divmod(mstime_remaining, 3600*24)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                mstime_remaining_text = self.tr("Expires in ")
                if days > 0:
                    mstime_remaining_text += "{days} days".format(days=days)
                else:
                    mstime_remaining_text += "{hours} hours and {min} min.".format(hours=hours,
                                                                                    min=minutes)

            status_value = self.tr("Member") if status else self.tr("Non-Member")
            status_color = '#00AA00' if status else self.tr('#FF0000')
            description = """<html>
            <body>
            <p>
            <span style=" font-size:16pt; font-weight:600;">{currency}</span>
            </p>
            <p>{nb_members} {members_label}</p>
            <p><span style="font-weight:600;">{monetary_mass_label}</span> : {monetary_mass}</p>
            <p><span style="font-weight:600;">{status_label}</span> : <span style="color:{status_color};">{status}</span></p>
            <p><span style="font-weight:600;">{nb_certs_label}</span> : {nb_certs} ({outdistanced_text})</p>
            <p><span style="font-weight:600;">{mstime_remaining_label}</span> : {mstime_remaining}</p>
            <p><span style="font-weight:600;">{balance_label}</span> : {balance}</p>
            </body>
            </html>""".format(currency=self.community.currency,
                              nb_members=len(members_pubkeys),
                              members_label=self.tr("members"),
                              monetary_mass_label=self.tr("Monetary mass"),
                              monetary_mass=localized_monetary_mass,
                              status_color=status_color,
                              status_label=self.tr("Status"),
                              status=status_value,
                              nb_certs_label=self.tr("Certs. received"),
                              nb_certs=nb_certs,
                              outdistanced_text=outdistanced_text,
                              mstime_remaining_label=self.tr("Membership"),
                              mstime_remaining=mstime_remaining_text,
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
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
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
        self.grabMouse()
        self.setStyleSheet(CommunityTile._pressed_stylesheet)
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.releaseMouse()
        self.setStyleSheet(CommunityTile._hover_stylesheet)
        self.clicked.emit()
        return super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(CommunityTile._hover_stylesheet)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(CommunityTile._standard_stylesheet)
        return super().leaveEvent(event)
