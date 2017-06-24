from sakia.errors import NoPeerAvailable
from sakia.data.processors import BlockchainProcessor
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt, \
                        QDateTime, QModelIndex, QLocale, QT_TRANSLATE_NOOP
from PyQt5.QtGui import QColor, QIcon, QFont
import logging
import asyncio


class IdentitiesFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.blockchain_processor = BlockchainProcessor.instanciate(app)

    def columnCount(self, parent):
        return len(IdentitiesTableModel.columns_ids) - 1
    
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
            expiration_col = IdentitiesTableModel.columns_ids.index('expiration')
            expiration_index = self.sourceModel().index(source_index.row(), expiration_col)

            STATUS_NOT_MEMBER = 0
            STATUS_MEMBER = 1
            STATUS_UNKNOWN = 2
            STATUS_EXPIRE_SOON = 3
            status = STATUS_NOT_MEMBER
            expiration_data = self.sourceModel().data(expiration_index, Qt.DisplayRole)
            current_time = QDateTime().currentDateTime().toMSecsSinceEpoch()
            sig_validity = self.sourceModel().sig_validity()
            warning_expiration_time = int(sig_validity / 3)
            #logging.debug("{0} > {1}".format(current_time, expiration_data))

            if expiration_data == 0:
                status = STATUS_UNKNOWN
            elif expiration_data is not None:
                status = STATUS_MEMBER
                if current_time > (expiration_data*1000):
                    status = STATUS_NOT_MEMBER
                elif current_time > ((expiration_data*1000) - (warning_expiration_time*1000)):
                    status = STATUS_EXPIRE_SOON

            if role == Qt.DisplayRole:
                if source_index.column() in (IdentitiesTableModel.columns_ids.index('renewed'),
                                             IdentitiesTableModel.columns_ids.index('expiration')):
                    if source_data:
                        ts = self.blockchain_processor.adjusted_ts(self.app.currency, source_data)
                        return QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(ts).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        ) + " BAT"
                    else:
                        return ""
                if source_index.column() == IdentitiesTableModel.columns_ids.index('publication'):
                    if source_data:
                        ts = self.blockchain_processor.adjusted_ts(self.app.currency, source_data)
                        return QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(ts),
                            QLocale.dateTimeFormat(QLocale(), QLocale.LongFormat)
                        ) + " BAT"
                    else:
                        return ""
                if source_index.column() == IdentitiesTableModel.columns_ids.index('pubkey'):
                    return source_data
                if source_index.column() == IdentitiesTableModel.columns_ids.index('block'):
                    return str(source_data)[:20]

            if role == Qt.ForegroundRole:
                if status == STATUS_EXPIRE_SOON:
                    return QColor("darkorange").darker(120)
                elif status == STATUS_NOT_MEMBER:
                    return QColor(Qt.red)
                elif status == STATUS_UNKNOWN:
                    return QColor(Qt.black)
                else:
                    return QColor(Qt.blue)

            if role == Qt.FontRole and status == STATUS_UNKNOWN:
                font = QFont()
                font.setItalic(True)
                return font

            if role == Qt.DecorationRole and source_index.column() == IdentitiesTableModel.columns_ids.index('uid'):
                if status == STATUS_NOT_MEMBER:
                    return QIcon(":/icons/not_member")
                elif status == STATUS_MEMBER:
                    return QIcon(":/icons/member")
                elif status == STATUS_EXPIRE_SOON:
                    return QIcon(":/icons/member_warning")

            return source_data


class IdentitiesTableModel(QAbstractTableModel):

    """
    A Qt abstract item model to display communities in a tree
    """

    columns_titles = {'uid': lambda: QT_TRANSLATE_NOOP("IdentitiesTableModel", 'UID'),
                           'pubkey': lambda: QT_TRANSLATE_NOOP("IdentitiesTableModel", 'Pubkey'),
                           'renewed': lambda: QT_TRANSLATE_NOOP("IdentitiesTableModel", 'Renewed'),
                           'expiration': lambda: QT_TRANSLATE_NOOP("IdentitiesTableModel", 'Expiration'),
                           'publication': lambda: QT_TRANSLATE_NOOP("IdentitiesTableModel", 'Publication Date'),
                           'block': lambda: QT_TRANSLATE_NOOP("IdentitiesTableModel", 'Publication Block'), }
    columns_ids = ('uid', 'pubkey', 'renewed', 'expiration', 'publication', 'block', 'identity')

    def __init__(self, parent, blockchain_service, identities_service):
        """
        Constructor
        :param parent:
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        :param sakia.services.IdentitiesService identities_service: the identities service
        """
        super().__init__(parent)
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service
        self.identities_data = []
        self._sig_validity = 0

    def sig_validity(self):
        return self._sig_validity
    
    @property
    def pubkeys(self):
        """
        Get pubkeys of displayed identities
        """
        return [i[1] for i in self.identities_data]

    def identity_data(self, identity):
        """
        Return the identity in the form a tuple to display
        :param sakia.data.entities.Identity identity: The identity to get data from
        :return: The identity data in the form of a tuple
        :rtype: tuple
        """
        join_date = identity.membership_timestamp
        expiration_date = self.identities_service.expiration_date(identity)
        sigdate_ts = identity.timestamp
        sigdate_block = identity.blockstamp
        name = "✴ " if identity.sentry else ""
        name += identity.uid

        return name, identity.pubkey, join_date, expiration_date, sigdate_ts, sigdate_block, identity

    def refresh_identities(self, identities):
        """
        Change the identities to display

        :param list[sakia.data.entities.Identity] identities: The new identities to display
        """
        logging.debug("Refresh {0} identities".format(len(identities)))
        self.beginResetModel()
        identities_data = []
        for identity in identities:
            identities_data.append(self.identity_data(identity))

        if len(identities) > 0:
            parameters = self.blockchain_service.parameters()
            self._sig_validity = parameters.sig_validity
        self.identities_data = identities_data
        self.endResetModel()

    def identity_loaded(self, identity):
        for i, idty in enumerate(self.identities_data):
            if idty[IdentitiesTableModel.columns_ids.index('identity')] == identity:
                self.identities_data[i] = self.identity_data(identity)
                self.dataChanged.emit(self.index(i, 0), self.index(i, len(IdentitiesTableModel.columns_ids)))
                return

    def rowCount(self, parent):
        return len(self.identities_data)

    def columnCount(self, parent):
        return len(IdentitiesTableModel.columns_ids)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            col_id = IdentitiesTableModel.columns_ids[section]
            return IdentitiesTableModel.columns_titles[col_id]()

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            identity_data = self.identities_data[row]
            return identity_data[col]

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
