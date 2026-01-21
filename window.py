from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

import logic
from budget_dialog import BudgetDialog


@dataclass(frozen=True)
class Expense:
	id: str
	name: str
	date: str
	price: str
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
			# Colonne 2 = Date (Id, Nom, Date, ...)
			idx = model.index(source_row, 2, source_parent)
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
		# Colonne 2 = Date (Id, Nom, Date, ...)
		if left.column() == 2 and right.column() == 2:
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
	def __init__(
		self,
		categories: list[str],
		parent: QtWidgets.QWidget | None = None,
		*,
		title: str = "Ajouter une dépense",
		initial: dict[str, str] | None = None,
	):
		super().__init__(parent)
		self.setWindowTitle(title)
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
		items = sorted(categories, key=str.casefold)
		# Si l'élément à éditer utilise une catégorie inconnue, l'ajouter pour pouvoir la sélectionner.
		if initial and initial.get("category") and initial["category"] not in items:
			items = [initial["category"].strip()] + items
		self.category_combo.addItems(items)
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

		if initial:
			self.name_edit.setText(initial.get("name", ""))
			self.date_edit.setText(initial.get("date", ""))
			self.price_edit.setText(initial.get("price", ""))
			self.description_edit.setText(initial.get("description", ""))
			category = (initial.get("category", "") or "").strip()
			if category:
				idx = self.category_combo.findText(category, QtCore.Qt.MatchFlag.MatchFixedString)
				if idx >= 0:
					self.category_combo.setCurrentIndex(idx)

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

			# Format actuel: [id, name, date, price, category, description]
			# Ancien format toléré: [name, date, price, category, description]
			expense_id = ""
			if len(row) >= 6:
				expense_id = (row[0] if len(row) >= 1 else "").strip()
				name = (row[1] if len(row) >= 2 else "").strip()
				date = (row[2] if len(row) >= 3 else "").strip()
				price = (row[3] if len(row) >= 4 else "").strip()
				category = (row[4] if len(row) >= 5 else "").strip()
				description = (row[5] if len(row) >= 6 else "").strip()
			else:
				name = (row[0] if len(row) >= 1 else "").strip()
				date = (row[1] if len(row) >= 2 else "").strip()
				price = (row[2] if len(row) >= 3 else "").strip()
				category = (row[3] if len(row) >= 4 else "").strip()
				description = (row[4] if len(row) >= 5 else "").strip()

			# Ignorer les lignes incomplètes
			if not name or not date or not category:
				continue

			expenses.append(
				Expense(
					id=expense_id,
					name=name,
					date=date,
					price=price,
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
		self._budgets_path = Path(__file__).resolve().parent / "saveCompte" / "budgets.json"
		self._categories, self._category_colors = logic.load_category_options(
			self._options_path
		)
		self._categories = sorted(self._categories, key=str.casefold)
		self._budgets = logic.load_budgets(self._budgets_path)

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

		self.delete_button = QtWidgets.QPushButton("Supprimer")
		self.delete_button.clicked.connect(self._on_delete_clicked)
		header_layout.addWidget(self.delete_button)

		self.manage_categories_button = QtWidgets.QPushButton("Catégories")
		self.manage_categories_button.clicked.connect(self._on_manage_categories_clicked)
		header_layout.addWidget(self.manage_categories_button)

		self.budget_button = QtWidgets.QPushButton("Budget")
		self.budget_button.clicked.connect(self._on_budget_clicked)
		header_layout.addWidget(self.budget_button)

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

		self.summary_layout = QtWidgets.QHBoxLayout()
		self.summary_layout.setSpacing(10)
		root_layout.addLayout(self.summary_layout)

		self.pivot_group = QtWidgets.QGroupBox("Totaux par mois / catégorie")
		pivot_layout = QtWidgets.QVBoxLayout(self.pivot_group)
		pivot_layout.setContentsMargins(8, 8, 8, 8)
		pivot_layout.setSpacing(6)

		# Tableau pivot: 12 lignes (mois) + 2 lignes synthèse, colonnes dynamiques = catégories + Total
		self.pivot_table = QtWidgets.QTableWidget(14, 2)
		self.pivot_table.setHorizontalHeaderLabels(["Mois", "Total"])
		self.pivot_table.horizontalHeader().setStretchLastSection(True)
		self.pivot_table.verticalHeader().setVisible(False)
		self.pivot_table.setEditTriggers(
			QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
		)
		self.pivot_table.setSelectionMode(
			QtWidgets.QAbstractItemView.SelectionMode.NoSelection
		)
		self.pivot_table.setAlternatingRowColors(True)
		self.pivot_table.setMinimumHeight(280)

		for i in range(12):
			month_item = QtWidgets.QTableWidgetItem(f"{i + 1:02d}")
			self.pivot_table.setItem(i, 0, month_item)
		# 2 lignes de synthèse
		self.pivot_table.setItem(12, 0, QtWidgets.QTableWidgetItem("Total à date"))
		self.pivot_table.setItem(13, 0, QtWidgets.QTableWidgetItem("Projection fin d'année"))

		pivot_layout.addWidget(self.pivot_table)

		self.summary_layout.addWidget(self.pivot_group, stretch=1)

		self.status = QtWidgets.QStatusBar()
		self.setStatusBar(self.status)

		self._source_model = QtGui.QStandardItemModel(0, 6, self)
		self._source_model.setHorizontalHeaderLabels(
			["Id", "Nom", "Date", "Prix", "Catégorie", "Description"]
		)

		self._proxy = ExpensesProxyModel(self)
		self._proxy.setSourceModel(self._source_model)
		self.table.setModel(self._proxy)
		self.table.doubleClicked.connect(self._on_table_double_clicked)
		self.table.setColumnHidden(0, True)

		self._expenses_cache: list[Expense] = []

		# Valeurs par défaut: année + mois actuels
		current = QtCore.QDate.currentDate()
		self._default_year = current.year()
		self._default_month = current.month()
		self._month_names = [
			"Janvier",
			"Février",
			"Mars",
			"Avril",
			"Mai",
			"Juin",
			"Juillet",
			"Août",
			"Septembre",
			"Octobre",
			"Novembre",
			"Décembre",
		]

		self.reload()

	def _selected_year_or_current(self) -> int:
		year_text = self.year_combo.currentText().strip() if self.year_combo.count() else "Tous"
		if year_text and year_text != "Tous":
			try:
				return int(year_text)
			except ValueError:
				pass
		return QtCore.QDate.currentDate().year()

	def _on_budget_clicked(self) -> None:
		year = self._selected_year_or_current()
		year_key = str(year)
		initial = self._budgets.get(year_key, {})

		dlg = BudgetDialog(
			year=year,
			categories=self._categories,
			month_names=self._month_names,
			initial_budgets=initial,
			parent=self,
		)
		if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
			return

		try:
			self._budgets[year_key] = dlg.budgets()
			logic.save_budgets(self._budgets_path, self._budgets)
		except ValueError as exc:
			QtWidgets.QMessageBox.warning(self, "Erreur", str(exc))
			return
		self._update_pivot_totals()

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

	def _on_table_double_clicked(self, index: QtCore.QModelIndex) -> None:
		if not index.isValid():
			return

		source_index = self._proxy.mapToSource(index)
		row = source_index.row()
		if row < 0:
			return

		def _text_at(col: int) -> str:
			idx = self._source_model.index(row, col)
			return str(idx.data() or "")

		old = {
			"id": _text_at(0),
			"name": _text_at(1),
			"date": _text_at(2),
			"price": "",
			"category": _text_at(4),
			"description": _text_at(5),
		}

		price_idx = self._source_model.index(row, 3)
		price_raw = price_idx.data(QtCore.Qt.ItemDataRole.UserRole)
		old["price"] = str(price_raw) if price_raw is not None else _text_at(3)

		dlg = AddExpenseDialog(
			self._categories,
			self,
			title="Modifier une dépense",
			initial=old,
		)
		if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
			return

		values = dlg.get_values()
		try:
			logic.update_expense(
				self._csv_path,
				expense_id=old["id"],
				new=[
					values["name"],
					values["date"],
					values["price"],
					values["category"],
					values["description"],
				],
			)
		except logic.DuplicateExpenseError as exc:
			QtWidgets.QMessageBox.warning(self, "Doublon", str(exc))
			return
		except ValueError as exc:
			QtWidgets.QMessageBox.warning(self, "Erreur", str(exc))
			return
		self.reload()

	def _on_delete_clicked(self) -> None:
		selection = self.table.selectionModel()
		if selection is None or not selection.hasSelection():
			return

		proxy_index = self.table.currentIndex()
		if not proxy_index.isValid():
			return

		source_index = self._proxy.mapToSource(proxy_index)
		row = source_index.row()
		if row < 0:
			return

		expense_id = str(self._source_model.index(row, 0).data() or "").strip()
		if not expense_id:
			QtWidgets.QMessageBox.warning(self, "Erreur", "Id de dépense introuvable")
			return

		confirm = QtWidgets.QMessageBox.question(
			self,
			"Confirmation",
			"Supprimer la dépense sélectionnée ?",
			QtWidgets.QMessageBox.StandardButton.Yes
			| QtWidgets.QMessageBox.StandardButton.No,
		)
		if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
			return

		try:
			logic.delete_expense(self._csv_path, expense_id=expense_id)
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
			self._update_pivot_totals()
			return

		self.month_combo.setEnabled(True)
		try:
			year = int(year_text)
		except ValueError:
			self._proxy.setYearMonthFilter(None, None)
			self._update_status()
			self._update_pivot_totals()
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
		self._update_pivot_totals()

	def _update_pivot_totals(self) -> None:
		"""Met à jour un tableau pivot: 1 ligne/mois, colonnes = catégories + Total."""

		year_text = (
			self.year_combo.currentText().strip() if self.year_combo.count() else "Tous"
		)
		year: int | None
		if year_text == "Tous" or year_text == "":
			year = None
		else:
			try:
				year = int(year_text)
			except ValueError:
				year = None

		# Colonnes = toutes les catégories connues + celles présentes dans les dépenses
		category_set: set[str] = set(self._categories)
		for exp in self._expenses_cache:
			cat = (exp.category or "").strip()
			if cat:
				category_set.add(cat)
			else:
				category_set.add("(Sans catégorie)")
		categories = sorted(category_set, key=str.casefold)
		year_key = str(year) if year is not None else ""
		budgets_for_year: dict[str, dict[str, float]] = (
			self._budgets.get(year_key, {}) if year_key else {}
		)

		headers = ["Mois", *categories, "Total"]
		self.pivot_table.setColumnCount(len(headers))
		self.pivot_table.setHorizontalHeaderLabels(headers)
		self.pivot_table.horizontalHeader().setStretchLastSection(True)
		self.pivot_table.setRowCount(14)

		# cumuls[month_index][category] = total
		cumuls: list[dict[str, float]] = [dict() for _ in range(12)]
		for exp in self._expenses_cache:
			date = QtCore.QDate.fromString(exp.date, "dd/MM/yyyy")
			if not date.isValid():
				continue
			if year is not None and date.year() != year:
				continue
			try:
				value = float(logic.parse_price_to_float(exp.price))
			except Exception:
				continue
			m = date.month() - 1
			if not (0 <= m < 12):
				continue
			cat = (exp.category or "").strip()
			if not cat:
				cat = "(Sans catégorie)"
			cumuls[m][cat] = cumuls[m].get(cat, 0.0) + value

		annual_total = 0.0
		monthly_totals: list[float] = [0.0] * 12
		for m in range(12):
			month_item = self.pivot_table.item(m, 0)
			if month_item is None:
				month_item = QtWidgets.QTableWidgetItem(self._month_names[m])
				self.pivot_table.setItem(m, 0, month_item)
			else:
				month_item.setText(self._month_names[m])

			row_total = 0.0
			month_budget_total = 0.0
			month_expenses_on_budget_total = 0.0
			month_has_any_budget = False
			for ci, cat in enumerate(categories, start=1):
				val = cumuls[m].get(cat, 0.0)
				row_total += val
				cell = self.pivot_table.item(m, ci)
				if cell is None:
					cell = QtWidgets.QTableWidgetItem()
					self.pivot_table.setItem(m, ci, cell)
				cell.setText(f"{val:.2f}")

				# Budget / reste (tooltip + surbrillance si dépassement)
				budget = 0.0
				budget_set = False
				if year is not None:
					month_key = f"{m + 1:02d}"
					month_budgets = budgets_for_year.get(month_key)
					if isinstance(month_budgets, dict) and cat in month_budgets:
						budget = float(month_budgets.get(cat) or 0.0)
						budget_set = True
				if budget_set:
					month_has_any_budget = True
					month_budget_total += budget
					month_expenses_on_budget_total += float(val)
					remaining = budget - float(val)
					# Afficher le reste (budget - dépenses)
					cell.setText(f"{remaining:.2f}")
					cell.setToolTip(
						f"Budget: {budget:.2f}\nDépenses: {float(val):.2f}\nReste: {remaining:.2f}"
					)
					cell.setBackground(QtGui.QBrush())
					if remaining < 0:
						cell.setForeground(QtGui.QBrush(QtGui.QColor("#b92020")))
					elif remaining > 0:
						cell.setForeground(QtGui.QBrush(QtGui.QColor("#008000")))
					else:
						cell.setForeground(QtGui.QBrush())
				else:
					cell.setToolTip("")
					cell.setBackground(QtGui.QBrush())
					cell.setForeground(QtGui.QBrush())

			total_col = len(headers) - 1
			total_item = self.pivot_table.item(m, total_col)
			if total_item is None:
				total_item = QtWidgets.QTableWidgetItem()
				self.pivot_table.setItem(m, total_col, total_item)

			# Si au moins un budget existe ce mois, le Total devient "reste total" sur les catégories budgétées.
			if month_has_any_budget:
				remaining_total = month_budget_total - month_expenses_on_budget_total
				total_item.setText(f"{remaining_total:.2f}")
				total_item.setToolTip(
					f"Budget total: {month_budget_total:.2f}\nDépenses: {month_expenses_on_budget_total:.2f}\nReste: {remaining_total:.2f}"
				)
				# Couleur standard pour le reste: vert si positif, rouge si négatif
				if remaining_total < 0:
					total_item.setForeground(QtGui.QBrush(QtGui.QColor("#b92020")))
				elif remaining_total > 0:
					total_item.setForeground(QtGui.QBrush(QtGui.QColor("#008000")))
				else:
					total_item.setForeground(QtGui.QBrush())
			else:
				total_item.setToolTip("")
				total_item.setText(f"{row_total:.2f}")
				# Couleur "dépenses": rouge si >0, vert si <0
				if row_total > 0:
					total_item.setForeground(QtGui.QBrush(QtGui.QColor("#b92020")))
				elif row_total < 0:
					total_item.setForeground(QtGui.QBrush(QtGui.QColor("#008000")))
				else:
					total_item.setForeground(QtGui.QBrush())

			annual_total += row_total
			monthly_totals[m] = row_total

		label_year = year_text if year is not None else "Tous"
		self.pivot_group.setTitle(f"Totaux par mois / catégorie ({label_year})")

		# Lignes synthèse
		current = QtCore.QDate.currentDate()
		is_current_year = year is not None and year == current.year()
		months_elapsed = current.month() if is_current_year else 12
		if months_elapsed < 1:
			months_elapsed = 1

		total_to_date = sum(monthly_totals[:months_elapsed])
		# Deuxième ligne: total sur l'année complète (Janvier → Décembre)
		projection_year_end = annual_total

		# Labels
		row_to_date = 12
		row_proj = 13
		label_to_date = "Total à date"
		if is_current_year:
			label_to_date = f"Total à date (jusqu'à {self._month_names[months_elapsed - 1]})"
		label_proj = "Total année (jusqu'à Décembre)"

		label_item_1 = self.pivot_table.item(row_to_date, 0)
		if label_item_1 is None:
			label_item_1 = QtWidgets.QTableWidgetItem()
			self.pivot_table.setItem(row_to_date, 0, label_item_1)
		label_item_1.setText(label_to_date)

		label_item_2 = self.pivot_table.item(row_proj, 0)
		if label_item_2 is None:
			label_item_2 = QtWidgets.QTableWidgetItem()
			self.pivot_table.setItem(row_proj, 0, label_item_2)
		label_item_2.setText(label_proj)

		# Totaux par catégorie sur les lignes synthèse
		to_date_by_cat: dict[str, float] = {c: 0.0 for c in categories}
		annual_by_cat: dict[str, float] = {c: 0.0 for c in categories}
		to_date_budget_by_cat: dict[str, float] = {c: 0.0 for c in categories}
		annual_budget_by_cat: dict[str, float] = {c: 0.0 for c in categories}

		# Si on a une année sélectionnée, on peut calculer des restes via budgets.
		use_budgets_for_totals = year is not None and bool(budgets_for_year)
		for m in range(12):
			month_key = f"{m + 1:02d}"
			month_budgets = budgets_for_year.get(month_key, {}) if use_budgets_for_totals else {}
			for c in categories:
				expense_val = float(cumuls[m].get(c, 0.0))
				annual_by_cat[c] += expense_val
				if m < months_elapsed:
					to_date_by_cat[c] += expense_val

				# Budget défini même si valeur = 0 (présence de la clé)
				if use_budgets_for_totals and isinstance(month_budgets, dict) and c in month_budgets:
					b = float(month_budgets.get(c) or 0.0)
					annual_budget_by_cat[c] += b
					if m < months_elapsed:
						to_date_budget_by_cat[c] += b

		proj_by_cat = dict(annual_by_cat)

		def _set_summary_cell(row_idx: int, col_idx: int, value: float) -> None:
			item = self.pivot_table.item(row_idx, col_idx)
			if item is None:
				item = QtWidgets.QTableWidgetItem()
				self.pivot_table.setItem(row_idx, col_idx, item)
			item.setText(f"{value:.2f}")
			font = item.font()
			font.setBold(True)
			item.setFont(font)
			# Pour les totaux "reste": vert si >0, rouge si <0
			if value > 0:
				item.setForeground(QtGui.QBrush(QtGui.QColor("#008000")))
			elif value < 0:
				item.setForeground(QtGui.QBrush(QtGui.QColor("#b92020")))
			else:
				item.setForeground(QtGui.QBrush())

		for ci, cat in enumerate(categories, start=1):
			if use_budgets_for_totals and (
				annual_budget_by_cat.get(cat, 0.0) != 0.0
				or (f"{1:02d}" in budgets_for_year)
			):
				# reste = budget - dépenses
				to_date_remaining = to_date_budget_by_cat.get(cat, 0.0) - to_date_by_cat.get(cat, 0.0)
				year_remaining = annual_budget_by_cat.get(cat, 0.0) - annual_by_cat.get(cat, 0.0)
				_set_summary_cell(row_to_date, ci, to_date_remaining)
				_set_summary_cell(row_proj, ci, year_remaining)
				cell_to_date = self.pivot_table.item(row_to_date, ci)
				cell_year = self.pivot_table.item(row_proj, ci)
				if cell_to_date:
					cell_to_date.setToolTip(
						f"Budget: {to_date_budget_by_cat.get(cat, 0.0):.2f}\nDépenses: {to_date_by_cat.get(cat, 0.0):.2f}"
					)
				if cell_year:
					cell_year.setToolTip(
						f"Budget: {annual_budget_by_cat.get(cat, 0.0):.2f}\nDépenses: {annual_by_cat.get(cat, 0.0):.2f}"
					)
			else:
				# Fallback: afficher les dépenses si pas de budget
				_set_summary_cell(row_to_date, ci, to_date_by_cat.get(cat, 0.0))
				_set_summary_cell(row_proj, ci, proj_by_cat.get(cat, 0.0))

		# Mettre les totaux dans la dernière colonne
		def _set_summary_total(row_idx: int, value: float) -> None:
			total_col = len(headers) - 1
			item = self.pivot_table.item(row_idx, total_col)
			if item is None:
				item = QtWidgets.QTableWidgetItem()
				self.pivot_table.setItem(row_idx, total_col, item)
			item.setText(f"{value:.2f}")
			font = item.font()
			font.setBold(True)
			item.setFont(font)
			# Pour les totaux "reste": vert si >0, rouge si <0
			if value > 0:
				item.setForeground(QtGui.QBrush(QtGui.QColor("#008000")))
			elif value < 0:
				item.setForeground(QtGui.QBrush(QtGui.QColor("#b92020")))
			else:
				item.setForeground(QtGui.QBrush())

		if use_budgets_for_totals:
			# Total reste = budget_total - dépenses_total (sur catégories budgétées)
			to_date_budget_total = sum(to_date_budget_by_cat.values())
			year_budget_total = sum(annual_budget_by_cat.values())
			to_date_remaining_total = to_date_budget_total - total_to_date
			year_remaining_total = year_budget_total - projection_year_end
			_set_summary_total(row_to_date, to_date_remaining_total)
			_set_summary_total(row_proj, year_remaining_total)
			item1 = self.pivot_table.item(row_to_date, len(headers) - 1)
			item2 = self.pivot_table.item(row_proj, len(headers) - 1)
			if item1:
				item1.setToolTip(
					f"Budget: {to_date_budget_total:.2f}\nDépenses: {total_to_date:.2f}"
				)
			if item2:
				item2.setToolTip(
					f"Budget: {year_budget_total:.2f}\nDépenses: {projection_year_end:.2f}"
				)
		else:
			_set_summary_total(row_to_date, total_to_date)
			_set_summary_total(row_proj, projection_year_end)

	def _update_status(self) -> None:
		total_rows = self._source_model.rowCount()
		visible_rows = self._proxy.rowCount()
		if self.search_edit.text().strip():
			self.status.showMessage(f"{visible_rows} / {total_rows} dépenses (filtrées)")
		else:
			self.status.showMessage(f"{total_rows} dépenses")

	def reload(self) -> None:
		self._source_model.removeRows(0, self._source_model.rowCount())
		# Migration automatique: ajoute un id unique à chaque ligne si nécessaire.
		try:
			logic.migrate_expense_ids(self._csv_path)
		except Exception as exc:
			QtWidgets.QMessageBox.warning(self, "Erreur", str(exc))
			return

		expenses = read_expenses(self._csv_path)
		self._expenses_cache = list(expenses)
		# Mettre à jour les filtres année/mois à partir des dates existantes
		years: set[int] = set()
		for exp in expenses:
			date = QtCore.QDate.fromString(exp.date, "dd/MM/yyyy")
			if date.isValid():
				years.add(date.year())

		years.add(self._default_year)
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
			price_display = exp.price
			try:
				price_display = logic.format_price(exp.price)
			except Exception:
				# Afficher brut si le prix ne se parse pas
				price_display = exp.price

			id_item = QtGui.QStandardItem(exp.id)
			name_item = QtGui.QStandardItem(exp.name)
			date_item = QtGui.QStandardItem(exp.date)
			price_item = QtGui.QStandardItem(price_display)
			# Conserver l'expression brute pour l'édition.
			price_item.setData(exp.price, QtCore.Qt.ItemDataRole.UserRole)
			category_item = QtGui.QStandardItem(exp.category)
			description_item = QtGui.QStandardItem(exp.description)

			items = [
				id_item,
				name_item,
				date_item,
				price_item,
				category_item,
				description_item,
			]
			for item in items:
				item.setEditable(False)
				if brush is not None:
					item.setBackground(brush)
			self._source_model.appendRow(items)

		self._update_status()
		self._update_pivot_totals()


def main() -> None:
	app = QtWidgets.QApplication([])
	app.setApplicationName("Compte - Dépenses")

	csv_path = Path(__file__).resolve().parent / "saveCompte" / "expenses.csv"
	window = ExpensesWindow(csv_path)
	window.showMaximized()
	raise SystemExit(app.exec())


if __name__ == "__main__":
	main()
