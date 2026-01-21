from __future__ import annotations

from typing import Any

_LANG = "fr"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        # App
        "app.name": "Compte - Dépenses",
        "window.title": "Dépenses",
        "window.expense_list": "Liste des dépenses",
        "window.totals_group": "Totaux par mois / catégorie",
        "window.restore_title": "Récupérer une sauvegarde",
        "window.restore_confirm": "Remplacer expenses.csv par:\n{filename} ?",
        "window.restore_missing": "Fichier introuvable",
        "window.restore_label": "Récupérer…",
        "window.reload_label": "Recharger",
        "window.add_label": "Ajouter",
        "window.delete_label": "Supprimer",
        "window.categories_label": "Catégories",
        "window.budget_label": "Budget",
        "window.search_placeholder": "Rechercher (nom, date, catégorie, description)",
        "window.language_label": "Langue",
        "window.context_edit": "Modifier…",
        "window.context_delete": "Supprimer",
        "window.pivot_month": "Mois",
        "window.pivot_total": "Total",
        "window.pivot_total_to_date": "Total à date",
        "window.pivot_year_projection": "Projection fin d'année",

        # Months
        "month.01": "Janvier",
        "month.02": "Février",
        "month.03": "Mars",
        "month.04": "Avril",
        "month.05": "Mai",
        "month.06": "Juin",
        "month.07": "Juillet",
        "month.08": "Août",
        "month.09": "Septembre",
        "month.10": "Octobre",
        "month.11": "Novembre",
        "month.12": "Décembre",

        # Pivot
        "pivot.uncategorized": "(Sans catégorie)",
        "pivot.group_title": "Totaux par mois / catégorie ({year})",
        "pivot.tooltip.cell": "Budget: {budget:.2f}\nDépenses: {expenses:.2f}\nReste: {remaining:.2f}",
        "pivot.tooltip.total": "Budget total: {budget:.2f}\nDépenses: {expenses:.2f}\nReste: {remaining:.2f}",
        "pivot.tooltip.summary": "Budget: {budget:.2f}\nDépenses: {expenses:.2f}",
        "pivot.label_to_date": "Total à date",
        "pivot.label_to_date_until": "Total à date (jusqu'à {month})",
        "pivot.label_year_total": "Total année (jusqu'à Décembre)",
        # Dialog common
        "dialog.error": "Erreur",
        "dialog.duplicate": "Doublon",
        "dialog.confirmation": "Confirmation",
        "dialog.restore": "Récupération",
        "dialog.categories": "Catégories",
        "dialog.budget": "Budget",
        "dialog.warning": "Avertissement",
        # Table headers
        "filter.all": "Tous",
        "col.id": "Id",
        "col.name": "Nom",
        "col.date": "Date",
        "col.price": "Prix",
        "col.category": "Catégorie",
        "col.description": "Description",
        "col.color": "Couleur",
        # Messages
        "msg.category_exists": "Cette catégorie existe déjà",
        "msg.confirm_delete_category": "Supprimer la catégorie '{name}' ?",
        "msg.confirm_delete_expense": "Supprimer la dépense sélectionnée ?",
        "msg.expense_id_missing": "Id de dépense introuvable",
        "msg.no_category": "Aucune catégorie disponible. Ajoute-en une dans 'Catégories'.",
        "msg.select_expense": "Sélectionne une dépense dans la liste.",
        "status.filtered": "{visible} / {total} dépenses (filtrées)",
        "status.total": "{total} dépenses",
        # Tooltips
        "tt.search": "Filtrer la liste des dépenses.",
        "tt.year": "Filtrer par année.",
        "tt.month": "Filtrer par mois (si une année est sélectionnée).",
        "tt.add": "Ajouter une nouvelle dépense.",
        "tt.delete": "Supprimer la dépense sélectionnée.",
        "tt.categories": "Gérer les catégories et leurs couleurs.",
        "tt.budget": "Définir/éditer les budgets mensuels.",
        "tt.reload": "Recharger depuis le fichier expenses.csv.",
        "tt.restore": "Restaurer expenses.csv depuis une sauvegarde.",
        "tt.language": "Choisir la langue de l'interface.",
        "tt.table": "Double-clic: modifier. Clic droit: menu.",
        # Add/Edit expense dialog
        "dlg.add.title": "Ajouter une dépense",
        "dlg.edit.title": "Modifier une dépense",
        "fld.name": "Nom",
        "fld.date": "Date",
        "fld.category": "Catégorie",
        "fld.price": "Prix",
        "fld.description": "Description",
        "ph.name": "Ex: Courses",
        "ph.date": "JJ/MM/AAAA",
        "ph.price": "Ex: 12.50",
        "ph.description": "Ex: supermarché",
        "tt.fld.name": "Nom de la dépense.",
        "tt.fld.date": "Date au format JJ/MM/AAAA.",
        "tt.fld.category": "Catégorie utilisée pour le tri et les totaux.",
        "tt.fld.price": "Prix (nombre) ou calcul (ex: 10+5).",
        "tt.fld.description": "Détails optionnels (magasin, note, etc.).",
        # Manage categories dialog
        "dlg.categories.title": "Gérer les catégories",
        "dlg.categories.col_name": "Catégorie",
        "dlg.categories.col_color": "Couleur",
        "btn.add": "Ajouter",
        "btn.remove": "Supprimer",
        "btn.color": "Couleur…",
        "btn.close": "Fermer",
        "ph.new_category": "Nouvelle catégorie",
        "tt.new_category": "Nom de la nouvelle catégorie.",
        "tt.add_category": "Ajouter la catégorie.",
        "tt.remove_category": "Supprimer la catégorie sélectionnée.",
        "tt.pick_color": "Choisir une couleur pour la catégorie.",
        "dlg.categories.choose_color": "Choisir une couleur",
        "dlg.categories.color_for": "Couleur pour '{name}'",
        # Budget dialog
        "dlg.budget.info": "Saisis un budget par mois et par catégorie.\nTu peux entrer un nombre ou un calcul (ex: 100+20).",
        "dlg.budget.copy_row": "Copier la ligne",
        "dlg.budget.paste_row": "Coller sur lignes sélectionnées",
        "dlg.budget.apply_year": "Appliquer sur l'année…",
        "dlg.budget.apply_selection": "Appliquer à la sélection…",
        "budget.title": "Budgets {year}",
        "budget.msg.select_cells": "Sélectionne une ou plusieurs cases budget (pas la colonne Mois).",
        "budget.msg.select_column": "Sélectionne au moins une cellule dans une colonne catégorie.",
        "budget.prompt.apply": "Valeur à appliquer (nombre ou calcul, vide pour effacer):",
        "budget.prompt.apply_year": "Valeur mensuelle à appliquer sur Jan→Déc (nombre ou calcul, vide pour effacer):",
    },
    "en": {
        # App
        "app.name": "Account - Expenses",
        "window.title": "Expenses",
        "window.expense_list": "Expenses list",
        "window.totals_group": "Totals by month / category",
        "window.restore_title": "Restore a backup",
        "window.restore_confirm": "Replace expenses.csv with:\n{filename} ?",
        "window.restore_missing": "File not found",
        "window.restore_label": "Restore…",
        "window.reload_label": "Reload",
        "window.add_label": "Add",
        "window.delete_label": "Delete",
        "window.categories_label": "Categories",
        "window.budget_label": "Budget",
        "window.search_placeholder": "Search (name, date, category, description)",
        "window.language_label": "Language",
        "window.context_edit": "Edit…",
        "window.context_delete": "Delete",
        "window.pivot_month": "Month",
        "window.pivot_total": "Total",
        "window.pivot_total_to_date": "Total to date",
        "window.pivot_year_projection": "Year-end projection",

        # Months
        "month.01": "January",
        "month.02": "February",
        "month.03": "March",
        "month.04": "April",
        "month.05": "May",
        "month.06": "June",
        "month.07": "July",
        "month.08": "August",
        "month.09": "September",
        "month.10": "October",
        "month.11": "November",
        "month.12": "December",

        # Pivot
        "pivot.uncategorized": "(Uncategorized)",
        "pivot.group_title": "Totals by month / category ({year})",
        "pivot.tooltip.cell": "Budget: {budget:.2f}\nExpenses: {expenses:.2f}\nRemaining: {remaining:.2f}",
        "pivot.tooltip.total": "Total budget: {budget:.2f}\nExpenses: {expenses:.2f}\nRemaining: {remaining:.2f}",
        "pivot.tooltip.summary": "Budget: {budget:.2f}\nExpenses: {expenses:.2f}",
        "pivot.label_to_date": "Total to date",
        "pivot.label_to_date_until": "Total to date (through {month})",
        "pivot.label_year_total": "Year total (through December)",
        # Dialog common
        "dialog.error": "Error",
        "dialog.duplicate": "Duplicate",
        "dialog.confirmation": "Confirmation",
        "dialog.restore": "Restore",
        "dialog.categories": "Categories",
        "dialog.budget": "Budget",
        "dialog.warning": "Warning",
        # Table headers
        "filter.all": "All",
        "col.id": "Id",
        "col.name": "Name",
        "col.date": "Date",
        "col.price": "Price",
        "col.category": "Category",
        "col.description": "Description",
        "col.color": "Color",
        # Messages
        "msg.category_exists": "This category already exists",
        "msg.confirm_delete_category": "Delete category '{name}' ?",
        "msg.confirm_delete_expense": "Delete the selected expense ?",
        "msg.expense_id_missing": "Expense id not found",
        "msg.no_category": "No categories available. Add one in 'Categories'.",
        "msg.select_expense": "Select an expense in the list.",
        "status.filtered": "{visible} / {total} expenses (filtered)",
        "status.total": "{total} expenses",
        # Tooltips
        "tt.search": "Filter the expenses list.",
        "tt.year": "Filter by year.",
        "tt.month": "Filter by month (when a year is selected).",
        "tt.add": "Add a new expense.",
        "tt.delete": "Delete the selected expense.",
        "tt.categories": "Manage categories and their colors.",
        "tt.budget": "Define/edit monthly budgets.",
        "tt.reload": "Reload from expenses.csv.",
        "tt.restore": "Restore expenses.csv from a backup.",
        "tt.language": "Choose UI language.",
        "tt.table": "Double-click: edit. Right-click: menu.",
        # Add/Edit expense dialog
        "dlg.add.title": "Add an expense",
        "dlg.edit.title": "Edit an expense",
        "fld.name": "Name",
        "fld.date": "Date",
        "fld.category": "Category",
        "fld.price": "Price",
        "fld.description": "Description",
        "ph.name": "e.g. Groceries",
        "ph.date": "DD/MM/YYYY",
        "ph.price": "e.g. 12.50",
        "ph.description": "e.g. supermarket",
        "tt.fld.name": "Expense name.",
        "tt.fld.date": "Date in DD/MM/YYYY format.",
        "tt.fld.category": "Category used for totals and filters.",
        "tt.fld.price": "Price (number) or expression (e.g. 10+5).",
        "tt.fld.description": "Optional details (store, note, etc.).",
        # Manage categories dialog
        "dlg.categories.title": "Manage categories",
        "dlg.categories.col_name": "Category",
        "dlg.categories.col_color": "Color",
        "btn.add": "Add",
        "btn.remove": "Remove",
        "btn.color": "Color…",
        "btn.close": "Close",
        "ph.new_category": "New category",
        "tt.new_category": "New category name.",
        "tt.add_category": "Add the category.",
        "tt.remove_category": "Remove selected category.",
        "tt.pick_color": "Pick a color for the category.",
        "dlg.categories.choose_color": "Choose a color",
        "dlg.categories.color_for": "Color for '{name}'",
        # Budget dialog
        "dlg.budget.info": "Enter a budget per month and per category.\nYou can type a number or an expression (e.g. 100+20).",
        "dlg.budget.copy_row": "Copy row",
        "dlg.budget.paste_row": "Paste to selected rows",
        "dlg.budget.apply_year": "Apply to year…",
        "dlg.budget.apply_selection": "Apply to selection…",
        "budget.title": "Budgets {year}",
        "budget.msg.select_cells": "Select one or more budget cells (not the Month column).",
        "budget.msg.select_column": "Select at least one cell in a category column.",
        "budget.prompt.apply": "Value to apply (number or expression, empty to clear):",
        "budget.prompt.apply_year": "Monthly value to apply Jan→Dec (number or expression, empty to clear):",
    },
}

LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    ("fr", "Français"),
    ("en", "English"),
]


def set_language(lang: str) -> None:
    global _LANG
    lang = (lang or "").strip().lower()
    if lang not in TRANSLATIONS:
        lang = "fr"
    _LANG = lang


def get_language() -> str:
    return _LANG


def tr(key: str, default: str | None = None, /, **fmt: Any) -> str:
    lang = _LANG if _LANG in TRANSLATIONS else "fr"
    value = TRANSLATIONS.get(lang, {}).get(key)
    if value is None:
        value = TRANSLATIONS.get("fr", {}).get(key)
    if value is None:
        value = default if default is not None else key
    if fmt:
        try:
            return value.format(**fmt)
        except Exception:
            return value
    return value
