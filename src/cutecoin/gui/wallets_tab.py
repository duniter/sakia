'''
Created on 15 févr. 2015

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QDateTime
from ..core.person import Person
from ..models.wallets import WalletsTableModel
from ..tools.exceptions import MembershipNotFoundError
from ..gen_resources.wallets_tab_uic import Ui_WalletsTab


class WalletsTabWidget(QWidget, Ui_WalletsTab):
    '''
    classdocs
    '''

    def __init__(self, account, community):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.account = account
        self.community = community

        self.refresh()

    def refresh(self):
        parameters = self.community.get_parameters()
        last_renewal = ""
        expiration = ""
        certifiers = 0
        certified = 0

        try:
            person = Person.lookup(self.account.pubkey, self.community)
            membership = person.membership(self.community)
            certified = person.certified_by(self.community)
            certifiers = person.certifiers_of(self.community)

            renew_block = membership.block_number
            last_renewal = self.community.get_block(renew_block).mediantime
            expiration = last_renewal + parameters['sigValidity']
        except MembershipNotFoundError:
            pass
        date_renewal = QDateTime.fromTime_t(last_renewal).date().toString()
        date_expiration = QDateTime.fromTime_t(expiration).date().toString()

        # set infos in label
        self.label_general.setText(
            """
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """.format(
                    self.account.name, self.account.pubkey,
                    "Membership",
                    "Last renewal on {:}, expiration on {:}".format(date_renewal, date_expiration),
                    "Your web of trust :",
                    "Certified by : {0} ; Certifier of : {0}".format(len(certified),
                                                                     len(certifiers))
            )
        )

        amount = self.account.amount(self.community)
        maximum = self.community.monetary_mass

        # set infos in label
        self.label_balance.setText(
            """
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """.format("Your money share : ", "{:.2f}%".format(amount/maximum*100),
                       "Your part : ", "{:.2f} in [{:.2f} - {:.2f}]".format(self.get_referential_value(amount),
                                                                   self.get_referential_value(0),
                                                                   self.get_referential_value(maximum))
            )
        )

        wallets_model = WalletsTableModel(self.account, self.community)
        self.table_wallets.setModel(wallets_model)

    def get_referential_value(self, value):
        return self.account.units_to_ref(value, self.community)

    def get_referential_diff_value(self, value):
        return self.account.units_to_diff_ref(value, self.community)

    def get_referential_name(self):
        return self.account.ref_name(self.community.short_currency)
