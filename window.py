from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

import logic


@dataclass(frozen=True)
class Expense:
	name: str
	date: str
	category: str
	description: str


class ExpensesProxyModel(QtCore.QSortFilterProxyModel):
	def __init__(self, parent: QtCore.QObject | None = None):
		super().__init__(parent)
		self._search_text = ""
		self._year_filter: int | None = None
		self._month_filter: int | None = None

	def setSearchText(self, text: str) -> None:
		self._search_text = (text or "").strip()
		self.invalidateFilter()

	def setYearMonthFilter(self, year: int | None, month: int | None) -> None:
		self._year_filter = year
		self._month_filter = month
		self.invalidateFilter()

	def filterAcceptsRow(
		self, source_row: int, source_parent: QtCore.QModelIndex
	) -> bool:
		model = self.sourceModel()
		if model is None:
			return True

		# Recherche texte sur toutes les colonnes
		if self._search_text:
			needle = self._search_text.casefold()
			matched = False
			for col in range(model.columnCount()):
				idx = model.index(source_row, col, source_parent)
				val = str(idx.data() or "")
				if needle in val.casefold():
					matched = True
					break
				# continuer
			if not matched:
				return False

		# Filtre année/mois basé sur la colonne Date (index 1, format JJ/MM/AAAA)
		if self._year_filter is not None:
			idx = model.index(source_row, 1, source_parent)
			date_text = str(idx.data() or "")
			date = QtCore.QDate.fromString(date_text, "dd/MM/yyyy")
			if not date.isValid():
				return False
			if date.year() != self._year_filter:
				return False
			if self._month_filter is not None and date.month() != self._month_filter:
				return False

		return True

	def lessThan(
		self,
		left: QtCore.QModelIndex,
		right: QtCore.QModelIndex,
	) -> bool:
		# Colonne 1 = Date (format JJ/MM/AAAA). On trie chronologiquement: AAAA/MM/JJ.
		if left.column() == 1 and right.column() == 1:
			left_text = str(left.data() or "")
			right_text = str(right.data() or "")
			left_date = QtCore.QDate.fromString(left_text, "dd/MM/yyyy")
			right_date = QtCore.QDate.fromString(right_text, "dd/MM/yyyy")

			if left_date.isValid() and right_date.isValid():
				return left_date < right_date

			# Si une des dates est invalide, on retombe sur le tri texte.
			return left_text < right_text

		return super().lessThan(left, right)
class AddExpenseDialog(QtWidgets.QDialog):
	def __init__(self, categories: list[str], parent: QtWidgets.QWidget | None = None):
		super().__init__(parent)
		self.setWindowTitle("Ajouter une dépense")
		self.setModal(True)
		self.resize(520, 240)

		layout = QtWidgets.QVBoxLayout(self)
		form = QtWidgets.QFormLayout()
		layout.addLayout(form)

		self.name_edit = QtWidgets.QLineEdit()
		self.name_edit.setPlaceholderText("Ex: Courses")
		form.addRow("Nom", self.name_edit)

		self.date_edit = QtWidgets.QLineEdit()
		self.date_edit.setPlaceholderText("JJ/MM/AAAA")
		form.addRow("Date", self.date_edit)

		self.category_combo = QtWidgets.QComboBox()
		self.category_combo.addItems(sorted(categories, key=str.casefold))
		form.addRow("Catégorie", self.category_combo)

		self.price_edit = QtWidgets.QLineEdit()
		self.price_edit.setPlaceholderText("Ex: 12.50")
		form.addRow("Prix", self.price_edit)

		self.description_edit = QtWidgets.QLineEdit()
		self.description_edit.setPlaceholderText("Ex: supermarché")
		form.addRow("Description", self.description_edit)

		buttons = QtWidgets.QDialogButtonBox(
			QtWidgets.QDialogButtonBox.StandardButton.Cancel
			| QtWidgets.QDialogButtonBox.StandardButton.Ok
		)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

		self.name_edit.setFocus()

	def get_values(self) -> dict[str, str]:
		return {
			"name": self.name_edit.text(),
			"date": self.date_edit.text(),
			"category": self.category_combo.currentText(),
			"price": self.price_edit.text(),
			"description": self.description_edit.text(),
		}


class ManageCategoriesDialog(QtWidgets.QDialog):
	def __init__(
		self,
		categories: list[str],
		colors: dict[str, str],
		parent: QtWidgets.QWidget | None = None,
	):
		super().__init__(parent)
		self.setWindowTitle("Gérer les catégories")
		self.setModal(True)
		self.resize(520, 360)

		self._colors: dict[str, str] = dict(colors)

		layout = QtWidgets.QVBoxLayout(self)

		self.table = QtWidgets.QTableWidget(0, 2)
		self.table.setHorizontalHeaderLabels(["Catégorie", "Couleur"])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.verticalHeader().setVisible(False)
		self.table.setSelectionBehavior(
			QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
		)
		self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
		self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
		layout.addWidget(self.table, stretch=1)

		for name in sorted(categories, key=str.casefold):
			self._append_row(name, self._colors.get(name, ""))

		actions = QtWidgets.QHBoxLayout()
		layout.addLayout(actions)

		self.new_category_edit = QtWidgets.QLineEdit()
		self.new_category_edit.setPlaceholderText("Nouvelle catégorie")
		actions.addWidget(self.new_category_edit, stretch=1)

		self.add_button = QtWidgets.QPushButton("Ajouter")
		self.add_button.clicked.connect(self._on_add)
		actions.addWidget(self.add_button)

		self.color_button = QtWidgets.QPushButton("Couleur…")
		self.color_button.clicked.connect(self._on_pick_color)
		actions.addWidget(self.color_button)

		self.remove_button = QtWidgets.QPushButton("Supprimer")
		self.remove_button.clicked.connect(self._on_remove)
		actions.addWidget(self.remove_button)

		buttons = QtWidgets.QDialogButtonBox(
			QtWidgets.QDialogButtonBox.StandardButton.Close
		)
		buttons.rejected.connect(self.reject)
		buttons.accepted.connect(self.accept)
		layout.addWidget(buttons)

	def categories(self) -> list[str]:
		return sorted(
			[
			self.table.item(row, 0).text()
			for row in range(self.table.rowCount())
			if self.table.item(row, 0)
		],
			key=str.casefold,
		)

	def colors(self) -> dict[str, str]:
		result: dict[str, str] = {}
		for row in range(self.table.rowCount()):
			name_item = self.table.item(row, 0)
			color_item = self.table.item(row, 1)
			if not name_item:
				continue
			name = name_item.text()
			color = ""
			if color_item:
				color = str(color_item.data(QtCore.Qt.ItemDataRole.UserRole) or "")
			result[name] = color
		return result

	def _append_row(self, name: str, color_hex: str) -> None:
		row = self.table.rowCount()
		self.table.insertRow(row)

		name_item = QtWidgets.QTableWidgetItem(name)
		self.table.setItem(row, 0, name_item)

		color_item = QtWidgets.QTableWidgetItem(color_hex or "")
		color_item.setData(QtCore.Qt.ItemDataRole.UserRole, color_hex or "")
		if color_hex:
			qcolor = QtGui.QColor(color_hex)
			color_item.setBackground(QtGui.QBrush(qcolor))
		self.table.setItem(row, 1, color_item)

	def _on_add(self) -> None:
		name = self.new_category_edit.text().strip()
		if not name:
			return
		if any(c.casefold() == name.casefold() for c in self.categories()):
			QtWidgets.QMessageBox.warning(self, "Erreur", "Cette catégorie existe déjà")
			return

		chosen = QtWidgets.QColorDialog.getColor(
			QtGui.QColor(self._colors.get(name, "#ffffff")),
			self,
			"Choisir une couleur",
		)
		color_hex = chosen.name() if chosen.isValid() else ""
		self._colors[name] = color_hex
		self._append_row(name, color_hex)
		self.table.sortItems(0, QtCore.Qt.SortOrder.AscendingOrder)
		self.new_category_edit.clear()

	def _on_pick_color(self) -> None:
		row = self.table.currentRow()
		if row < 0:
			return
		name_item = self.table.item(row, 0)
		if not name_item:
			return
		name = name_item.text()

		current_hex = self._colors.get(name, "")
		chosen = QtWidgets.QColorDialog.getColor(
			QtGui.QColor(current_hex or "#ffffff"),
			self,
			f"Couleur pour '{name}'",
		)
		if not chosen.isValid():
			return
		color_hex = chosen.name()
		self._colors[name] = color_hex

		color_item = self.table.item(row, 1)
		if not color_item:
			color_item = QtWidgets.QTableWidgetItem()
			self.table.setItem(row, 1, color_item)
		color_item.setText(color_hex)
		color_item.setData(QtCore.Qt.ItemDataRole.UserRole, color_hex)
		color_item.setBackground(QtGui.QBrush(QtGui.QColor(color_hex)))

	def _on_remove(self) -> None:
		row = self.table.currentRow()
		if row < 0:
			return
		name_item = self.table.item(row, 0)
		if not name_item:
			return
		name = name_item.text()

		confirm = QtWidgets.QMessageBox.question(
			self,
			"Confirmation",
			f"Supprimer la catégorie '{name}' ?",
			QtWidgets.QMessageBox.StandardButton.Yes
			| QtWidgets.QMessageBox.StandardButton.No,
		)
		if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
			return

		self.table.removeRow(row)
		self._colors.pop(name, None)


def read_expenses(csv_path: Path) -> list[Expense]:
	if not csv_path.exists():
		return []

	expenses: list[Expense] = []
	with csv_path.open(mode="r", encoding="utf-8", newline="") as file:
		reader = csv.reader(file)
		for row in reader:
			if not row:
				continue

			# Format actuel: [name, date, price, category, description]
			# On tolère des colonnes manquantes/supplémentaires.
			name = (row[0] if len(row) >= 1 else "").strip()
			date = (row[1] if len(row) >= 2 else "").strip()
			category = (row[3] if len(row) >= 4 else "").strip()
			description = (row[4] if len(row) >= 5 else "").strip()

			# Ignorer les lignes incomplètes
			if not (name or date or category or description):
				continue

			expenses.append(
				Expense(
					name=name,
					date=date,
					category=category,
					description=description,
				)
			)

	return expenses


class ExpensesWindow(QtWidgets.QMainWindow):
	def __init__(self, csv_path: Path):
		super().__init__()
		self._csv_path = csv_path
		self._options_path = Path(__file__).resolve().parent / "saveCompte" / "qt_options.json"
		self._categories, self._category_colors = logic.load_category_options(
			self._options_path
		)
		self._categories = sorted(self._categories, key=str.casefold)

		self.setWindowTitle("Dépenses")
		self.resize(1000, 650)

		central = QtWidgets.QWidget(self)
		self.setCentralWidget(central)

		root_layout = QtWidgets.QVBoxLayout(central)
		root_layout.setContentsMargins(12, 12, 12, 12)
		root_layout.setSpacing(10)

		header_layout = QtWidgets.QHBoxLayout()
		root_layout.addLayout(header_layout)

		title = QtWidgets.QLabel("Liste des dépenses")
		title_font = QtGui.QFont()
		title_font.setPointSize(14)
		title_font.setBold(True)
		title.setFont(title_font)
		header_layout.addWidget(title)

		header_layout.addStretch(1)

		self.search_edit = QtWidgets.QLineEdit()
		self.search_edit.setPlaceholderText("Rechercher (nom, date, catégorie, description)")
		self.search_edit.setClearButtonEnabled(True)
		self.search_edit.textChanged.connect(self._on_search_changed)
		header_layout.addWidget(self.search_edit, stretch=2)

		self.year_combo = QtWidgets.QComboBox()
		self.year_combo.currentIndexChanged.connect(self._on_year_month_changed)
		header_layout.addWidget(self.year_combo)

		self.month_combo = QtWidgets.QComboBox()
		self.month_combo.currentIndexChanged.connect(self._on_year_month_changed)
		header_layout.addWidget(self.month_combo)

		self.add_button = QtWidgets.QPushButton("Ajouter")
		self.add_button.clicked.connect(self._on_add_clicked)
		header_layout.addWidget(self.add_button)

		self.manage_categories_button = QtWidgets.QPushButton("Catégories")
		self.manage_categories_button.clicked.connect(self._on_manage_categories_clicked)
		header_layout.addWidget(self.manage_categories_button)

		self.reload_button = QtWidgets.QPushButton("Recharger")
		self.reload_button.clicked.connect(self.reload)
		header_layout.addWidget(self.reload_button)

		self.path_label = QtWidgets.QLabel(str(self._csv_path))
		self.path_label.setTextInteractionFlags(
			QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
		)
		self.path_label.setStyleSheet("color: #666;")
		root_layout.addWidget(self.path_label)

		self.table = QtWidgets.QTableView()
		self.table.setAlternatingRowColors(True)
		self.table.setSelectionBehavior(
			QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
		)
		self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
		self.table.setSortingEnabled(True)
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.horizontalHeader().setSectionResizeMode(
			QtWidgets.QHeaderView.ResizeMode.Interactive
		)
		self.table.verticalHeader().setVisible(False)
		root_layout.addWidget(self.table, stretch=1)

		self.status = QtWidgets.QStatusBar()
		self.setStatusBar(self.status)

		self._source_model = QtGui.QStandardItemModel(0, 4, self)
		self._source_model.setHorizontalHeaderLabels(
			["Nom", "Date", "Catégorie", "Description"]
		)

		self._proxy = ExpensesProxyModel(self)
		self._proxy.setSourceModel(self._source_model)
		self.table.setModel(self._proxy)

		# Valeurs par défaut: année + mois actuels
		current = QtCore.QDate.currentDate()
		self._default_year = current.year()
		self._default_month = current.month()

		self.reload()

	def _on_add_clicked(self) -> None:
		if not self._categories:
			QtWidgets.QMessageBox.warning(
				self,
				"Catégories",
				"Aucune catégorie disponible. Ajoute-en une dans 'Catégories'.",
			)
			return

		dlg = AddExpenseDialog(self._categories, self)
		if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
			return

		values = dlg.get_values()
		try:
			logic.add_expense(
				self._csv_path,
				name=values["name"],
				date=values["date"],
				price=values["price"],
				category=values["category"],
				description=values["description"],
			)
		except logic.DuplicateExpenseError as exc:
			QtWidgets.QMessageBox.warning(self, "Doublon", str(exc))
			return
		except ValueError as exc:
			QtWidgets.QMessageBox.warning(self, "Erreur", str(exc))
			return
		self.reload()

	def _on_manage_categories_clicked(self) -> None:
		dlg = ManageCategoriesDialog(self._categories, self._category_colors, self)
		dlg.exec()

		# Sauvegarder l'état courant (ajouts/suppressions) dans le fichier d'options
		new_categories = dlg.categories()
		try:
			logic.save_category_options(self._options_path, new_categories, dlg.colors())
			self._categories, self._category_colors = logic.load_category_options(
				self._options_path
			)
			self._categories = sorted(self._categories, key=str.casefold)
			self.reload()
		except Exception as exc:
			QtWidgets.QMessageBox.warning(self, "Erreur", str(exc))

	def _on_search_changed(self, text: str) -> None:
		self._proxy.setSearchText(text)
		self._update_status()

	def _on_year_month_changed(self) -> None:
		year_text = self.year_combo.currentText().strip() if self.year_combo.count() else "Tous"
		if year_text == "Tous" or year_text == "":
			self.month_combo.setCurrentText("Tous")
			self.month_combo.setEnabled(False)
			self._proxy.setYearMonthFilter(None, None)
			self._update_status()
			return

		self.month_combo.setEnabled(True)
		try:
			year = int(year_text)
		except ValueError:
			self._proxy.setYearMonthFilter(None, None)
			self._update_status()
			return

		month_text = self.month_combo.currentText().strip()
		month: int | None
		if month_text == "Tous" or month_text == "":
			month = None
		else:
			try:
				month = int(month_text)
			except ValueError:
				month = None

		self._proxy.setYearMonthFilter(year, month)
		self._update_status()

	def _update_status(self) -> None:
		total_rows = self._source_model.rowCount()
		visible_rows = self._proxy.rowCount()
		if self.search_edit.text().strip():
			self.status.showMessage(f"{visible_rows} / {total_rows} dépenses (filtrées)")
		else:
			self.status.showMessage(f"{total_rows} dépenses")

	def reload(self) -> None:
		self._source_model.removeRows(0, self._source_model.rowCount())

		expenses = read_expenses(self._csv_path)
		# Mettre à jour les filtres année/mois à partir des dates existantes
		years: set[int] = set()
		for exp in expenses:
			date = QtCore.QDate.fromString(exp.date, "dd/MM/yyyy")
			if date.isValid():
				years.add(date.year())

		sorted_years = sorted(years)
		previous_year = self.year_combo.currentText() if self.year_combo.count() else ""
		previous_month = self.month_combo.currentText() if self.month_combo.count() else ""

		self.year_combo.blockSignals(True)
		self.month_combo.blockSignals(True)
		self.year_combo.clear()
		self.year_combo.addItem("Tous")
		for y in sorted_years:
			self.year_combo.addItem(str(y))

		self.month_combo.clear()
		self.month_combo.addItem("Tous")
		for m in range(1, 13):
			self.month_combo.addItem(f"{m:02d}")

		# Défaut: année+mois actuels si disponibles, sinon restaurer la sélection.
		if str(self._default_year) in [str(y) for y in sorted_years]:
			self.year_combo.setCurrentText(str(self._default_year))
			self.month_combo.setCurrentText(f"{self._default_month:02d}")
		else:
			if previous_year:
				self.year_combo.setCurrentText(previous_year)
			if previous_month:
				self.month_combo.setCurrentText(previous_month)

		self.year_combo.blockSignals(False)
		self.month_combo.blockSignals(False)
		self._on_year_month_changed()
		for exp in expenses:
			row_color = self._category_colors.get(exp.category, "")
			brush: QtGui.QBrush | None = None
			if row_color:
				qcolor = QtGui.QColor(row_color)
				if qcolor.isValid():
					brush = QtGui.QBrush(qcolor)
			items = [
				QtGui.QStandardItem(exp.name),
				QtGui.QStandardItem(exp.date),
				QtGui.QStandardItem(exp.category),
				QtGui.QStandardItem(exp.description),
			]
			for item in items:
				item.setEditable(False)
				if brush is not None:
					item.setBackground(brush)
			self._source_model.appendRow(items)

		self._update_status()


def main() -> None:
	app = QtWidgets.QApplication([])
	app.setApplicationName("Compte - Dépenses")

	csv_path = Path(__file__).resolve().parent / "saveCompte" / "expenses.csv"
	window = ExpensesWindow(csv_path)
	window.show()
	raise SystemExit(app.exec())


if __name__ == "__main__":
	main()
