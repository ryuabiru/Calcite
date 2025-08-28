# pandas_model.py

import pandas as pd
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

class PandasModel(QAbstractTableModel):
    """
    pandasのDataFrameをQTableViewで表示・編集するためのモデルクラス。
    QAbstractTableModelを継承し、必要なメソッドをオーバーライドしている。
    """
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._sort_column = -1
        self._sort_order = Qt.SortOrder.AscendingOrder

    def rowCount(self, parent=None):
        """行数を返す"""
        return self._data.shape[0]

    def columnCount(self, parent=None):
        """列数を返す"""
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """指定されたインデックスとロールに対応するデータを返す"""
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """ヘッダーのデータを返す"""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None

    def setHeaderData(self, section, orientation, value, role):
        """
        ヘッダーのデータ（カラム名）が変更されたときに呼び出される。
        """
        if role == Qt.ItemDataRole.EditRole and orientation == Qt.Orientation.Horizontal:
            new_columns = self._data.columns.tolist()
            new_columns[section] = value
            self._data.columns = new_columns
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return super().setHeaderData(section, orientation, value, role)

    def sort(self, column, order):
        """DataFrameをソートする"""
        try:
            col_name = self._data.columns[column]
            
            self.layoutAboutToBeChanged.emit()
            self._data = self._data.sort_values(
                by=col_name,
                ascending=(order == Qt.SortOrder.AscendingOrder),
                kind='mergesort'
            ).reset_index(drop=True)
            self.layoutChanged.emit()
            
        except Exception as e:
            print(f"Sort error: {e}")

    def setData(self, index, value, role):
        """
        ユーザーによってセルのデータが編集されたときに呼び出される。
        """
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
        """すべてのセルを編集可能にするためのフラグを返す"""
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def refresh_model(self):
        """
        DataFrameの構造が大きく変更された後（列の追加・削除など）に
        ビュー全体を更新するために呼び出す。
        """
        self.layoutChanged.emit()

    def insertRows(self, row, count, parent=QModelIndex()):
        """指定された位置に行を挿入する"""
        self.beginInsertRows(parent, row, row + count - 1)
        
        df_top = self._data.iloc[:row]
        df_bottom = self._data.iloc[row:]
        df_new = pd.DataFrame(index=range(count), columns=self._data.columns).fillna('')
        
        self._data = pd.concat([df_top, df_new, df_bottom]).reset_index(drop=True)
        
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """指定された位置の行を削除する"""
        self.beginRemoveRows(parent, row, row + count - 1)
        
        self._data.drop(self._data.index[row:row+count], inplace=True)
        self._data.reset_index(drop=True, inplace=True)
        
        self.endRemoveRows()
        return True

    def insertColumns(self, col, count, parent=QModelIndex()):
        """指定された位置に列を挿入する"""
        self.beginInsertColumns(parent, col, col + count - 1)

        for i in range(count):
            new_col_name = f"Unnamed_{len(self._data.columns) + i}"
            self._data.insert(col + i, new_col_name, '')

        self.endInsertColumns()
        return True

    def removeColumns(self, col, count, parent=QModelIndex()):
        """指定された位置の列を削除する"""
        self.beginRemoveColumns(parent, col, col + count - 1)

        cols_to_drop = self._data.columns[col:col+count]
        self._data.drop(columns=cols_to_drop, inplace=True)

        self.endRemoveColumns()
        return True