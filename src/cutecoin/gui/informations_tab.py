"""
Created on 2 févr. 2014

@author: inso
"""

import logging
from PyQt5.QtWidgets import QWidget, QHeaderView
from PyQt5.QtCore import Qt
from ..models.parameters import ParametersModel
from ..gen_resources.informations_tab_uic import Ui_InformationsTabWidget


class InformationsTabWidget(QWidget, Ui_InformationsTabWidget):

    """
    classdocs
    """

    def __init__(self, account, community):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.community = community
        self.account = account

        self.table_general.HorizontalHeader = QHeaderView(Qt.Orientation(Qt.Horizontal))
        #self.table_general.HorizontalHeader.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_general.HorizontalHeader.setStretchLastSection(True)
        self.table_general.setHorizontalHeader(self.table_general.HorizontalHeader)
        self.table_general.horizontalHeader().hide()
        self.table_general.verticalHeader().hide()

        self.table_money.HorizontalHeader = QHeaderView(Qt.Orientation(Qt.Horizontal))
        #self.table_money.HorizontalHeader.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_money.HorizontalHeader.setStretchLastSection(True)
        self.table_money.setHorizontalHeader(self.table_money.HorizontalHeader)
        self.table_money.horizontalHeader().hide()
        self.table_money.verticalHeader().hide()

        self.table_wot.HorizontalHeader = QHeaderView(Qt.Orientation(Qt.Horizontal))
        #self.table_wot.HorizontalHeader.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_wot.HorizontalHeader.setStretchLastSection(True)
        self.table_wot.setHorizontalHeader(self.table_wot.HorizontalHeader)
        self.table_wot.horizontalHeader().hide()
        self.table_wot.verticalHeader().hide()

        self.display_tables()

    def display_tables(self):
        try:
            params = self.community.get_parameters()
        except Exception as e:
            logging.debug('community get_parameters error : ' + str(e))
            return False

        try:
            block = self.community.get_ud_block()
        except Exception as e:
            logging.debug('community get_ud_block error : ' + str(e))
            return False

        general = [
            {'name': 'dividend', 'value': block['dividend'],
             'description': 'Universal Dividend UD(t) in currency units'},
            {'name': 'monetaryMass', 'value': block['monetaryMass'],
             'description': 'Monetary Mass M(t) in currency units'},
            {'name': 'membersCount', 'value': block['membersCount'],
             'description': 'Members N(t)'},
            {'name': 'monetaryMassPerMember', 'value': "{:.2f}".format(block['monetaryMass'] / block['membersCount']),
             'description': 'Monetary Mass per member M(t)/N(t) in currency units'},
            {'name': 'actualGrowth',
             'value': "{:2.2%}".format(block['dividend'] / ((block['monetaryMass'] - (block['membersCount'] * block['dividend'])) / block['membersCount'])),
             'description': 'Actual % Growth (UD(t) / (M(t-1)/Nt))'}
        ]
        self.table_general.setModel(ParametersModel(general))
        update_table_height(self.table_general, len(general))

        money = [
            # money params
            {'name': 'c', 'value': "{:2.0%}".format(params['c']),
             'description': '% growth'},
            {'name': 'ud0', 'value': params['ud0'],
             'description': 'Initial Universal Dividend in currency units'},
            {'name': 'dt', 'value': params['dt'] / 86400,
             'description': 'Time period in days between two UD'},
            {'name': 'medianTimeBlocks', 'value': params['medianTimeBlocks'],
             'description': 'Number of blocks used for calculating median time'},
            {'name': 'avgGenTime', 'value': params['avgGenTime'],
             'description': 'The average time in seconds for writing 1 block (wished time)'},
            {'name': 'dtDiffEval', 'value': params['dtDiffEval'],
             'description': 'The number of blocks required to evaluate again PoWMin value'},
            {'name': 'blocksRot', 'value': params['blocksRot'],
             'description': 'The number of previous blocks to check for personalized difficulty'},
            {'name': 'percentRot', 'value': "{:2.0%}".format(params['percentRot']),
             'description': 'The percent of previous issuers to reach for personalized difficulty'}
        ]
        self.table_money.setModel(ParametersModel(money))
        update_table_height(self.table_money, len(money))

        wot = [
            # wot params
            {'name': 'sigDelay', 'value': params['sigDelay'] / 86400,
             'description': 'Minimum delay between 2 identical certifications (in days)'},
            {'name': 'sigValidity', 'value': params['sigValidity'] / 86400,
             'description': 'Maximum age of a valid signature (in days)'},
            {'name': 'sigQty', 'value': params['sigQty'],
             'description': 'Minimum quantity of signatures to be part of the WoT'},
            {'name': 'sigWoT', 'value': params['sigWoT'],
             'description': 'Minimum quantity of valid made certifications to be part of the WoT for distance rule'},
            {'name': 'msValidity', 'value': params['msValidity'] / 86400,
             'description': 'Maximum age of a valid membership (in days)'},
            {'name': 'stepMax', 'value': params['stepMax'],
             'description': 'Maximum distance between each WoT member and a newcomer'},
        ]
        self.table_wot.setModel(ParametersModel(wot))
        update_table_height(self.table_wot, len(wot))


def update_table_height(table, rows):
    row_height = table.rowHeight(0)
    table_height = (rows * row_height) + table.horizontalHeader().height() + (2 * table.frameWidth())
    table.setMinimumHeight(table_height)
    table.setMaximumHeight(table_height)
