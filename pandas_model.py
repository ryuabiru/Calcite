# pandas_model.py

import pandas as pd
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

    # ★--- カラム名変更を受け付けるメソッドを追加 ---★
    def setHeaderData(self, section, orientation, value, role):
        if role == Qt.ItemDataRole.EditRole and orientation == Qt.Orientation.Horizontal:
            new_columns = self._data.columns.tolist()
            new_columns[section] = value
            self._data.columns = new_columns
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return super().setHeaderData(section, orientation, value, role)

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

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        
        # DataFrameの途中に空行を挿入
        df_top = self._data.iloc[:row]
        df_bottom = self._data.iloc[row:]
        df_new = pd.DataFrame(index=range(count), columns=self._data.columns).fillna('') # 空の行を作成
        
        self._data = pd.concat([df_top, df_new, df_bottom]).reset_index(drop=True)
        
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        
        # 指定された行を削除
        self._data.drop(self._data.index[row:row+count], inplace=True)
        self._data.reset_index(drop=True, inplace=True)
        
        self.endRemoveRows()
        return True

    def insertColumns(self, col, count, parent=QModelIndex()):
        self.beginInsertColumns(parent, col, col + count - 1)

        # 新しい列を挿入
        for i in range(count):
            new_col_name = f"Unnamed_{len(self._data.columns) + i}"
            self._data.insert(col + i, new_col_name, '')

        self.endInsertColumns()
        return True

    def removeColumns(self, col, count, parent=QModelIndex()):
        self.beginRemoveColumns(parent, col, col + count - 1)

        # 指定された列を削除
        cols_to_drop = self._data.columns[col:col+count]
        self._data.drop(columns=cols_to_drop, inplace=True)

        self.endRemoveColumns()
        return True