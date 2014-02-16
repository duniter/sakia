'''
Created on 2 févr. 2014

@author: inso
'''
import logging
from math import pow

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFrame, QSlider, QLabel, QDialogButtonBox
from PyQt5.QtCore import Qt, QSignalMapper

from cutecoin.models.coin import Coin

from cutecoin.gen_resources.issuanceDialog_uic import Ui_IssuanceDialog

class IssuanceDialog(QDialog, Ui_IssuanceDialog):
    '''
    classdocs
    '''


    def __init__(self, issuer, community):
        '''
        Constructor
        '''
        super(IssuanceDialog, self).__init__()
        self.setupUi(self)
        self.issuer = issuer
        self.community = community
        self.dividend = self.community.dividend()
        self.coinMinimalPower = self.community.coinMinimalPower()
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.sliders = []
        self.slidersLabels = []
        maxCoinPower = 1
        nMax = 0
        # We look for the power of 10 which is directly higher than the dividend
        while maxCoinPower < self.dividend:
            maxCoinPower = pow(10, nMax)
            nMax += 1

        # N max is the power just before the one we found

        logging.debug("Pow max : " + str(nMax))

        for i in range(self.coinMinimalPower, nMax):
            self.generateSliderFrame(i)

    def generateSliderFrame(self, n):
        frame = QFrame(self)
        frame.setLayout(QVBoxLayout())

        label = QLabel(frame)
        frame.layout().addWidget(label)

        slider = QSlider(Qt.Horizontal, frame)
        slider.setMinimum(0)
        slider.setMaximum(9)
        slider.valueChanged.connect(self.refreshTotal)

        frame.layout().addWidget(slider)

        label.setText("0 coins of " + str(pow(10, n)))


        self.slidersLabels.append(label)
        self.sliders.append(slider)

        self.layout().insertWidget(n, frame)

    def refreshTotal(self):
        n = 0
        total = 0
        for slider in self.sliders:
            self.slidersLabels[n].setText(str(slider.value()) + " coins of " + str(pow(10, n)))
            self.totalLabel.setText("Total : " + str(total))
            total += slider.value()*pow(10, n)
            n += 1
        self.totalLabel.setText("Total : " + str(total))
        if total != self.dividend:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def actionIssueCoins(self):
        coins = []
        n = 0
        for slider in self.sliders:
            coins.append(str(slider.value())+","+str(n))
            n += 1
        self.issuer.issueDividend(self.community, coins)





