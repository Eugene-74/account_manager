from __future__ import annotations

import csv
import json
from pathlib import Path


class DuplicateExpenseError(ValueError):
    pass


DEFAULT_CATEGORIES = [
    "Nourriture",
    "Vie quotidienne",
    "Santé",
    "Loisir",
    "Vêtement",
    "Transport",
    "Coiffeur",
    "Épargne",
]


DEFAULT_CATEGORY_COLORS: dict[str, str] = {
    "Nourriture": "#FFC0CB",
    "Vie quotidienne": "#008080",
    "Santé": "#b92020",
    "Loisir": "#800080",
    "Vêtement": "#20b7b9",
    "Transport": "#808080",
    "Coiffeur": "#A52A2A",
    "Épargne": "#008000",
}


def _normalize_hex_color(color: str | None) -> str:
    if not isinstance(color, str):
        return ""
    value = color.strip()
    if not value:
        return ""
    if not value.startswith("#"):
        return ""
    if len(value) not in (4, 7):
        return ""
    # très léger contrôle: tous les chars doivent être hexa
    hex_part = value[1:]
    if any(ch not in "0123456789abcdefABCDEF" for ch in hex_part):
        return ""
    return value


def load_category_options(options_path: Path) -> tuple[list[str], dict[str, str]]:
    """Charge les catégories et leurs couleurs depuis qt_options.json.

    Format supporté (actuel):
      {"categories": [{"name": "Nourriture", "color": "#FFC0CB"}, ...]}

    Migration automatique depuis l'ancien format:
      {"categories": ["Nourriture", ...]}
    """

    options_path = Path(options_path)
    if not options_path.exists():
        categories = list(DEFAULT_CATEGORIES)
        colors = {c: DEFAULT_CATEGORY_COLORS.get(c, "") for c in categories}
        save_category_options(options_path, categories, colors)
        return categories, colors

    try:
        data = json.loads(options_path.read_text(encoding="utf-8"))
    except Exception:
        categories = list(DEFAULT_CATEGORIES)
        colors = {c: DEFAULT_CATEGORY_COLORS.get(c, "") for c in categories}
        save_category_options(options_path, categories, colors)
        return categories, colors

    if not isinstance(data, dict):
        categories = list(DEFAULT_CATEGORIES)
        colors = {c: DEFAULT_CATEGORY_COLORS.get(c, "") for c in categories}
        save_category_options(options_path, categories, colors)
        return categories, colors

    raw_categories = data.get("categories")
    categories: list[str] = []
    colors: dict[str, str] = {}
    seen: set[str] = set()

    # Ancien format: liste de strings
    if isinstance(raw_categories, list) and raw_categories and all(
        isinstance(x, str) for x in raw_categories
    ):
        for name in raw_categories:
            value = name.strip()
            if not value:
                continue
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            categories.append(value)
            colors[value] = DEFAULT_CATEGORY_COLORS.get(value, "")
        if not categories:
            categories = list(DEFAULT_CATEGORIES)
            colors = {c: DEFAULT_CATEGORY_COLORS.get(c, "") for c in categories}

        save_category_options(options_path, categories, colors)
        return categories, colors

    # Nouveau format: liste d'objets {name,color}
    if isinstance(raw_categories, list):
        for item in raw_categories:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not isinstance(name, str):
                continue
            value = name.strip()
            if not value:
                continue

            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)

            color = _normalize_hex_color(item.get("color"))
            if not color:
                color = DEFAULT_CATEGORY_COLORS.get(value, "")

            categories.append(value)
            colors[value] = color

    if not categories:
        categories = list(DEFAULT_CATEGORIES)
        colors = {c: DEFAULT_CATEGORY_COLORS.get(c, "") for c in categories}
        save_category_options(options_path, categories, colors)
        return categories, colors

    # normalisation persistée
    save_category_options(options_path, categories, colors)
    return categories, colors


def save_category_options(
    options_path: Path, categories: list[str], colors: dict[str, str]
) -> None:
    options_path = Path(options_path)
    options_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "categories": [
            {"name": name, "color": _normalize_hex_color(colors.get(name)) or ""}
            for name in categories
        ]
    }

    options_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_categories(options_path: Path) -> list[str]:
    categories, _colors = load_category_options(options_path)
    return categories


def save_categories(options_path: Path, categories: list[str]) -> None:
    # Compat: conserve les couleurs existantes si possible
    existing_categories, existing_colors = load_category_options(options_path)
    colors: dict[str, str] = {}
    for name in categories:
        if name in existing_colors:
            colors[name] = existing_colors[name]
        else:
            colors[name] = DEFAULT_CATEGORY_COLORS.get(name, "")
    save_category_options(options_path, categories, colors)


def add_category(options_path: Path, name: str) -> list[str]:
    name = name.strip()
    if not name:
        raise ValueError("Le nom de catégorie est obligatoire")

    categories = load_categories(options_path)
    if any(c.casefold() == name.casefold() for c in categories):
        raise ValueError("Cette catégorie existe déjà")

    categories.append(name)
    save_categories(options_path, categories)
    return categories


def remove_category(options_path: Path, name: str) -> list[str]:
    name = name.strip()
    if not name:
        raise ValueError("La catégorie à supprimer est invalide")

    categories = load_categories(options_path)
    remaining = [c for c in categories if c.casefold() != name.casefold()]
    if len(remaining) == len(categories):
        raise ValueError("Catégorie introuvable")

    save_categories(options_path, remaining)
    return remaining


def add_expense(
    csv_path: Path,
    *,
    name: str,
    date: str,
    price: str,
    category: str,
    description: str,
    allow_duplicates: bool = False,
) -> None:
    """Ajoute une dépense au format: name,date,price,category,description."""

    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    name = name.strip()
    date = date.strip()
    price = price.strip().replace(",", ".")
    category = category.strip()
    description = description.strip()

    if not name:
        raise ValueError("Le nom est obligatoire")
    if not date:
        raise ValueError("La date est obligatoire")
    if not category:
        raise ValueError("La catégorie est obligatoire")
    if price == "":
        price = "0"

    row = [name, date, price, category, description]

    if csv_path.exists() and not allow_duplicates:
        with csv_path.open(mode="r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            for existing in reader:
                if existing == row:
                    raise DuplicateExpenseError("Cette dépense existe déjà")

    with csv_path.open(mode="a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(row)
