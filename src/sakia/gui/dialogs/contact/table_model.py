
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel,\
    QModelIndex, QT_TRANSLATE_NOOP
from sakia.data.processors import ContactsProcessor


class ContactsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        """
        History of all transactions
        :param PyQt5.QtWidgets.QWidget parent: parent widget
        """
        super().__init__(parent)
        self.app = None

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None) - 1

    def setSourceModel(self, source_model):
        self.app = source_model.app
        super().setSourceModel(source_model)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        source_model = self.sourceModel()
        left_data = source_model.data(left, Qt.DisplayRole)
        right_data = source_model.data(right, Qt.DisplayRole)
        if left_data == right_data:
            txid_col = source_model.columns_types.index('contact_id')
            txid_left = source_model.index(left.row(), txid_col)
            txid_right = source_model.index(right.row(), txid_col)
            return txid_left < txid_right

        return left_data < right_data

    def contact_id(self, index):
        """
        Gets available table data at given index
        :param index:
        :return: tuple containing (Identity, Transfer)
        """
        if index.isValid() and index.row() < self.rowCount(QModelIndex()):
            source_index = self.mapToSource(index)
            contact_id_col = ContactsTableModel.columns_types.index('contact_id')
            contact_id = self.sourceModel().contacts_data[source_index.row()][contact_id_col]
            return contact_id
        return -1

    def data(self, index, role):
        source_index = self.mapToSource(index)
        model = self.sourceModel()
        source_data = model.data(source_index, role)
        return source_data


class ContactsTableModel(QAbstractTableModel):
    """
    A Qt abstract item model to display contacts in a table view
    """

    columns_types = (
        'name',
        'pubkey',
        'contact_id'
    )

    columns_headers = (
        QT_TRANSLATE_NOOP("ContactsTableModel", 'Name'),
        QT_TRANSLATE_NOOP("ContactsTableModel", 'Public key'),
    )

    def __init__(self, parent, app):
        """
        History of all transactions
        :param PyQt5.QtWidgets.QWidget parent: parent widget
        :param sakia.app.Application app: the main application
        """
        super().__init__(parent)
        self.app = app
        self.contacts_processor = ContactsProcessor.instanciate(app)
        self.contacts_data = []

    def add_or_edit_contact(self, contact):

        for i, data in enumerate(self.contacts_data):
            if data[ContactsTableModel.columns_types.index('contact_id')] == contact.contact_id:
                self.contacts_data[i] = self.data_contact(contact)
                self.dataChanged.emit(self.index(i, 0), self.index(i, len(ContactsTableModel.columns_types)))
                return
        else:
            self.beginInsertRows(QModelIndex(), len(self.contacts_data), len(self.contacts_data))
            self.contacts_data.append(self.data_contact(contact))
            self.endInsertRows()

    def remove_contact(self, contact):
        for i, data in enumerate(self.contacts_data):
            if data[ContactsTableModel.columns_types.index('contact_id')] == contact.contact_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self.contacts_data.pop(i)
                self.endRemoveRows()
                return

    def data_contact(self, contact):
        """
        Converts a contact to table data
        :param sakia.data.entities.Contact contact: the contact
        :return: data as tuple
        """
        return contact.name, contact.pubkey, contact.contact_id

    def init_contacts(self):
        self.beginResetModel()
        self.contacts_data = []
        contacts = self.contacts_processor.contacts()
        for contact in contacts:
            self.contacts_data.append(self.data_contact(contact))
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.contacts_data)

    def columnCount(self, parent):
        return len(ContactsTableModel.columns_types)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ContactsTableModel.columns_headers[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        if role in (Qt.DisplayRole, Qt.ForegroundRole, Qt.ToolTipRole):
            return self.contacts_data[row][col]

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

