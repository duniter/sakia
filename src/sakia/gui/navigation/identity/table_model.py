from sakia.errors import NoPeerAvailable
from sakia.data.entities import Identity, Certification
from sakia.data.processors import BlockchainProcessor
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt, \
                        QDateTime, QModelIndex, QLocale, QT_TRANSLATE_NOOP
from PyQt5.QtGui import QColor, QIcon, QFont
import logging
import asyncio


class CertifiersFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.blockchain_processor = BlockchainProcessor.instanciate(app)

    def columnCount(self, parent):
        return len(CertifiersTableModel.columns_ids) - 2

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        source_model = self.sourceModel()
        left_data = source_model.data(left, Qt.DisplayRole)
        right_data = source_model.data(right, Qt.DisplayRole)
        left_data = 0 if left_data is None else left_data
        right_data = 0 if right_data is None else right_data
        return left_data < right_data

    def data(self, index, role):
        source_index = self.mapToSource(index)
        if source_index.isValid():
            source_data = self.sourceModel().data(source_index, role)
            publication_col = CertifiersTableModel.columns_ids.index('publication')
            publication_index = self.sourceModel().index(source_index.row(), publication_col)
            expiration_col = CertifiersTableModel.columns_ids.index('expiration')
            expiration_index = self.sourceModel().index(source_index.row(), expiration_col)
            written_col = CertifiersTableModel.columns_ids.index('written')
            written_index = self.sourceModel().index(source_index.row(), written_col)

            publication_data = self.sourceModel().data(publication_index, Qt.DisplayRole)
            expiration_data = self.sourceModel().data(expiration_index, Qt.DisplayRole)
            written_data = self.sourceModel().data(written_index, Qt.DisplayRole)
            current_time = QDateTime().currentDateTime().toMSecsSinceEpoch()
            warning_expiration_time = int((expiration_data - publication_data) / 3)
            #logging.debug("{0} > {1}".format(current_time, expiration_data))

            if role == Qt.DisplayRole:
                if source_index.column() == CertifiersTableModel.columns_ids.index('expiration'):
                    if source_data:
                        ts = self.blockchain_processor.adjusted_ts(self.app.currency, source_data)
                        return QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(ts),
                            QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                        ) + " BAT"
                    else:
                        return ""
                if source_index.column() == CertifiersTableModel.columns_ids.index('publication'):
                    if source_data:
                        ts = self.blockchain_processor.adjusted_ts(self.app.currency, source_data)
                        return QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(ts),
                            QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                        ) + " BAT"
                    else:
                        return ""
                if source_index.column() == CertifiersTableModel.columns_ids.index('pubkey'):
                    return source_data

            if role == Qt.FontRole:
                font = QFont()
                if not written_data:
                    font.setItalic(True)
                return font

            if role == Qt.ForegroundRole:
                if current_time > ((expiration_data*1000) - (warning_expiration_time*1000)):
                    return QColor("darkorange").darker(120)

            return source_data


class CertifiersTableModel(QAbstractTableModel):

    """
    A Qt abstract item model to display communities in a tree
    """

    columns_titles = {'uid': lambda: QT_TRANSLATE_NOOP("CertifiersTableModel", 'UID'),
                           'pubkey': lambda: QT_TRANSLATE_NOOP("CertifiersTableModel", 'Pubkey'),
                           'publication': lambda: QT_TRANSLATE_NOOP("CertifiersTableModel", 'Publication Date'),
                           'expiration': lambda: QT_TRANSLATE_NOOP("CertifiersTableModel", 'Expiration'),
                           'available': lambda: QT_TRANSLATE_NOOP("CertifiersTableModel"), }
    columns_ids = ('uid', 'pubkey', 'publication', 'expiration', 'written', 'identity')

    def __init__(self, parent, connection, blockchain_service, identities_service):
        """
        Constructor
        :param parent:
        :param sakia.data.entities.Connection connection:
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        :param sakia.services.IdentitiesService identities_service: the identities service
        """
        super().__init__(parent)
        self.connection = connection
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service
        self._certifiers_data = list()

    def init_certifiers(self):
        """
        Init table with data to display
        """
        self.beginResetModel()
        certifications = self.identities_service.certifications_received(self.connection.pubkey)
        logging.debug("Refresh {0} certifiers".format(len(certifications)))
        certifiers_data = []
        for certifier in certifications:
            certifiers_data.append(self.certifier_data(certifier))

        self._certifiers_data = certifiers_data
        self.endResetModel()

    def certifier_data(self, certification: Certification) -> tuple:
        """
        Return the identity in the form a tuple to display
        :param Certification certification: The certification to get data from
        :return: The certification data in the form of a tuple
        :rtype: tuple
        """
        parameters = self.blockchain_service.parameters()
        publication_date = certification.timestamp
        written = certification.written_on >= 0

        if written:
            expiration_date = publication_date + parameters.sig_validity
        else:
            expiration_date = publication_date + parameters.sig_window

        identity = self.identities_service.get_identity(certification.certifier)
        if not identity:
            identity = Identity(currency=certification.currency, pubkey=certification.certifier, uid="")

        return identity.uid, identity.pubkey, publication_date, expiration_date, written, identity

    def certifier_loaded(self, identity: Identity):
        """
        Update identity of certifier after closing information window

        :param Identity identity: Updated identity of the certifier
        :return:
        """
        for i, certifier_data in enumerate(self._certifiers_data):
            if certifier_data[CertifiersTableModel.columns_ids.index('identity')] == identity:
                self._certifiers_data[i] = update_certifier_data_from_identity(certifier_data, identity)
                self.dataChanged.emit(self.index(i, 0), self.index(i, len(CertifiersTableModel.columns_ids)))
                return

    def rowCount(self, parent):
        return len(self._certifiers_data)

    def columnCount(self, parent):
        return len(CertifiersTableModel.columns_ids)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            col_id = CertifiersTableModel.columns_ids[section]
            return CertifiersTableModel.columns_titles[col_id]()

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            identity_data = self._certifiers_data[row]
            return identity_data[col]

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


#######################
# STATIC FUNCTIONS
#######################


def update_certifier_data_from_identity(certifier_data: tuple, identity: Identity) -> tuple:
    """
    Return certifier data from updated identity

    :param tuple certifier_data: Certifier data list
    :param Identity identity: Identity of the certifier
    :return tuple:
    """
    return identity.uid, \
        identity.pubkey, \
        certifier_data[CertifiersTableModel.columns_ids.index('publication')], \
        certifier_data[CertifiersTableModel.columns_ids.index('expiration')], \
        certifier_data[CertifiersTableModel.columns_ids.index('written')], \
        identity
