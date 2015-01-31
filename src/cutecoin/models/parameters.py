# -*- coding: utf-8 -*-

from PyQt5.QtCore import (Qt, QAbstractTableModel, QModelIndex)
from PyQt5.QtGui import QFont, QColor


class ParametersModel(QAbstractTableModel):

    def __init__(self, infos=list(), parent=None):
        super().__init__(parent)
        self.infos = infos

    def rowCount(self, index=QModelIndex()):
        """ Returns the number of rows the model holds. """
        return len(self.infos)

    def columnCount(self, index=QModelIndex()):
        """ Returns the number of columns the model holds. """
        return 3

    def data(self, index, role=Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
            returning data, return None
        """
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.infos):
            return None

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self.infos[index.row()]["name"]
            elif index.column() == 1:
                return self.infos[index.row()]["value"]
            elif index.column() == 2:
                return self.infos[index.row()]["description"]
        elif role == Qt.TextAlignmentRole and index.column() == 0:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.FontRole and index.column() == 0:
            font = QFont()
            font.setBold(True)
            return font
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """ Set the headers to be displayed. """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Name"
            elif section == 1:
                return "Value"

        return None

    def insertRows(self, position, rows=1, index=QModelIndex()):
        """ Insert a row into the model. """
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)

        for row in range(rows):
            self.infos.insert(position + row, {"name": "", "value": ""})

        self.endInsertRows()
        return True

    def removeRows(self, position, rows=1, index=QModelIndex()):
        """ Remove a row from the model. """
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)

        del self.infos[position:position+rows]

        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.EditRole):
        """ Adjust the data (set it to <value>) depending on the given
            index and role.
        """
        if role != Qt.EditRole:
            return False

        if index.isValid() and 0 <= index.row() < len(self.infos):
            info = self.infos[index.row()]
            if index.column() == 0:
                info["name"] = value
            elif index.column() == 1:
                info["value"] = value
            else:
                return False

            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're
            implementing this function just to see how it's done, as we
            manually adjust each tableView to have NoEditTriggers.
        """
        if not index.isValid():
            return Qt.ItemIsEnabled | Qt.Item
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index))

