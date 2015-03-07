import logging
import datetime
import math
from PyQt5.QtWidgets import QDialog
from ..gen_resources.member_uic import Ui_DialogMember


class MemberDialog(QDialog, Ui_DialogMember):
    """
    classdocs
    """

    def __init__(self, account, community, person):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.community = community
        self.account = account
        self.person = person
        self.label_uid.setText(person.name)

        join_date = self.person.get_join_date(self.community)
        if join_date is None:
            join_date = 'not a member'

        # set infos in label
        self.label_properties.setText(
            """
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></div></td><td>{:}</td></tr>
            </table>
            """.format(
                'Public key',
                self.person.pubkey,
                'Join date',
                join_date
            )
        )

