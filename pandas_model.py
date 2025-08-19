# pandas_model.py

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # The hyphen is corrected to a period here
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        # The hyphen is corrected to a period here
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None

    def setData(self, index, value, role):
        # The hyphen is corrected to a period here
        if role == Qt.ItemDataRole.EditRole:
            try:
                original_value = self._data.iloc[index.row(), index.column()]
                value = type(original_value)(value)
                self._data.iloc[index.row(), index.column()] = value
            except (ValueError, TypeError):
                self._data.iloc[index.row(), index.column()] = value
            
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable