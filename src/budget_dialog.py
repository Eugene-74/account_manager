from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from . import logic
from .translate import tr


class BudgetDialog(QtWidgets.QDialog):
	def __init__(
		self,
		*,
		year: int,
		categories: list[str],
		month_names: list[str],
		initial_budgets: dict[str, dict[str, float]] | None = None,
		parent: QtWidgets.QWidget | None = None,
	):
		super().__init__(parent)
		self.setWindowTitle(tr("budget.title", year=year))
		self.setModal(True)
		self.resize(900, 520)

		self._year = year
		self._categories = list(categories)
		self._month_names = list(month_names)
		self._initial = initial_budgets or {}

		layout = QtWidgets.QVBoxLayout(self)

		info = QtWidgets.QLabel(tr("dlg.budget.info"))
		info.setStyleSheet("color: #555;")
		layout.addWidget(info)

		self.table = QtWidgets.QTableWidget(12, 1 + len(self._categories))
		headers = ["Mois", *self._categories]
		self.table.setHorizontalHeaderLabels(headers)
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.verticalHeader().setVisible(False)
		self.table.setAlternatingRowColors(True)
		self.table.setSelectionBehavior(
			QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems
		)
		self.table.setSelectionMode(
			QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
		)
		layout.addWidget(self.table, stretch=1)

		actions = QtWidgets.QHBoxLayout()
		layout.addLayout(actions)
		self.copy_row_button = QtWidgets.QPushButton(tr("dlg.budget.copy_row"))
		self.copy_row_button.clicked.connect(self._copy_row)
		actions.addWidget(self.copy_row_button)

		self.paste_row_button = QtWidgets.QPushButton(tr("dlg.budget.paste_row"))
		self.paste_row_button.clicked.connect(self._paste_row_to_selected_rows)
		self.paste_row_button.setEnabled(False)
		actions.addWidget(self.paste_row_button)

		actions.addStretch(1)

		self.apply_year_button = QtWidgets.QPushButton(tr("dlg.budget.apply_year"))
		self.apply_year_button.clicked.connect(self._apply_to_year)
		actions.addWidget(self.apply_year_button)

		self.apply_button = QtWidgets.QPushButton(tr("dlg.budget.apply_selection"))
		self.apply_button.clicked.connect(self._apply_to_selection)
		actions.addWidget(self.apply_button)

		for m in range(12):
			self.table.setItem(m, 0, QtWidgets.QTableWidgetItem(self._month_names[m]))

		for m in range(12):
			month_key = f"{m + 1:02d}"
			per_cat = self._initial.get(month_key, {})
			for ci, cat in enumerate(self._categories, start=1):
				if cat in per_cat:
					val = float(per_cat.get(cat, 0.0) or 0.0)
					text = f"{val:.2f}"
				else:
					text = ""
				item = QtWidgets.QTableWidgetItem(text)
				item.setTextAlignment(
					QtCore.Qt.AlignmentFlag.AlignRight
					| QtCore.Qt.AlignmentFlag.AlignVCenter
				)
				self.table.setItem(m, ci, item)

		buttons = QtWidgets.QDialogButtonBox(
			QtWidgets.QDialogButtonBox.StandardButton.Cancel
			| QtWidgets.QDialogButtonBox.StandardButton.Ok
		)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

		self._shortcut_apply = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
		self._shortcut_apply.activated.connect(self._apply_current_to_selection)
		self._shortcut_apply2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Enter"), self)
		self._shortcut_apply2.activated.connect(self._apply_current_to_selection)

		self._copied_row: list[str] | None = None

	def budgets(self) -> dict[str, dict[str, float]]:
		"""Retourne {"01": {"Nourriture": 200.0, ...}, ...}."""

		result: dict[str, dict[str, float]] = {}
		for m in range(12):
			month_key = f"{m + 1:02d}"
			per_cat: dict[str, float] = {}
			for ci, cat in enumerate(self._categories, start=1):
				item = self.table.item(m, ci)
				text = item.text().strip() if item else ""
				if text == "":
					continue
				value = float(logic.parse_price_to_float(text))
				per_cat[cat] = value
			if per_cat:
				result[month_key] = per_cat
		return result

	def _selected_budget_indexes(self) -> list[QtCore.QModelIndex]:
		"""Retourne les indexes sélectionnés qui correspondent aux cellules budget (col>=1)."""
		indexes = self.table.selectionModel().selectedIndexes() if self.table.selectionModel() else []
		return [i for i in indexes if i.column() >= 1]

	def _apply_value_to_indexes(self, value_text: str, indexes: list[QtCore.QModelIndex]) -> None:
		text = (value_text or "").strip()
		if text == "":
			# Effacer
			for idx in indexes:
				item = self.table.item(idx.row(), idx.column())
				if item is None:
					item = QtWidgets.QTableWidgetItem("")
					self.table.setItem(idx.row(), idx.column(), item)
				item.setText("")
			return

		value = float(logic.parse_price_to_float(text))
		display = f"{value:.2f}"
		for idx in indexes:
			item = self.table.item(idx.row(), idx.column())
			if item is None:
				item = QtWidgets.QTableWidgetItem()
				self.table.setItem(idx.row(), idx.column(), item)
			item.setText(display)

	def _apply_to_selection(self) -> None:
		indexes = self._selected_budget_indexes()
		if not indexes:
			QtWidgets.QMessageBox.information(
				self,
				tr("dialog.budget"),
				tr("budget.msg.select_cells"),
			)
			return

		text, ok = QtWidgets.QInputDialog.getText(
			self,
			tr("dlg.budget.apply_selection"),
			tr("budget.prompt.apply"),
		)
		if not ok:
			return
		try:
			self._apply_value_to_indexes(text, indexes)
		except ValueError as exc:
			QtWidgets.QMessageBox.warning(self, tr("dialog.error"), str(exc))

	def _apply_to_year(self) -> None:
		# Applique une valeur sur 12 mois pour les colonnes (catégories) sélectionnées.
		indexes = self._selected_budget_indexes()
		cols = {i.column() for i in indexes}
		if not cols:
			current = self.table.currentIndex()
			if current.isValid() and current.column() >= 1:
				cols = {current.column()}
		if not cols:
			QtWidgets.QMessageBox.information(
				self,
				tr("dialog.budget"),
				tr("budget.msg.select_column"),
			)
			return

		text, ok = QtWidgets.QInputDialog.getText(
			self,
			tr("dlg.budget.apply_year"),
			tr("budget.prompt.apply_year"),
		)
		if not ok:
			return

		all_indexes: list[QtCore.QModelIndex] = []
		for row in range(12):
			for col in cols:
				all_indexes.append(self.table.model().index(row, col))
		try:
			self._apply_value_to_indexes(text, all_indexes)
		except ValueError as exc:
			QtWidgets.QMessageBox.warning(self, tr("dialog.error"), str(exc))

	def _copy_row(self) -> None:
		row = self.table.currentRow()
		if row < 0:
			return
		values: list[str] = []
		for ci in range(1, 1 + len(self._categories)):
			item = self.table.item(row, ci)
			values.append(item.text() if item else "")
		self._copied_row = values
		self.paste_row_button.setEnabled(True)

	def _paste_row_to_selected_rows(self) -> None:
		if not self._copied_row:
			return
		indexes = self.table.selectionModel().selectedIndexes() if self.table.selectionModel() else []
		rows = sorted({i.row() for i in indexes if 0 <= i.row() < 12})
		if not rows:
			row = self.table.currentRow()
			if 0 <= row < 12:
				rows = [row]
		if not rows:
			return

		for r in rows:
			for offset, text in enumerate(self._copied_row, start=1):
				item = self.table.item(r, offset)
				if item is None:
					item = QtWidgets.QTableWidgetItem()
					self.table.setItem(r, offset, item)
				item.setText(text)

	def _apply_current_to_selection(self) -> None:
		indexes = self._selected_budget_indexes()
		if not indexes:
			return
		current = self.table.currentIndex()
		if not current.isValid() or current.column() < 1:
			return
		item = self.table.item(current.row(), current.column())
		text = item.text().strip() if item else ""
		try:
			self._apply_value_to_indexes(text, [i for i in indexes if i != current])
		except ValueError as exc:
			QtWidgets.QMessageBox.warning(self, tr("dialog.error"), str(exc))
