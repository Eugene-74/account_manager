from __future__ import annotations

import csv
import json
import ast
import uuid
from pathlib import Path


class DuplicateExpenseError(ValueError):
    pass


def _eval_arithmetic_expression(expr: str) -> float:
    """Évalue une expression arithmétique simple en toute sécurité.

    Supporte: +, -, *, /, parenthèses et nombres.
    Ex: "4+5*6" -> 34
    """

    expr = (expr or "").strip()
    if not expr:
        raise ValueError("Prix invalide")

    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Prix invalide") from exc

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return _eval(n.body)

        # Python 3.11+: literals are ast.Constant
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)

        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            value = _eval(n.operand)
            return value if isinstance(n.op, ast.UAdd) else -value

        if isinstance(n, ast.BinOp) and isinstance(
            n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
        ):
            left = _eval(n.left)
            right = _eval(n.right)
            if isinstance(n.op, ast.Add):
                return left + right
            if isinstance(n.op, ast.Sub):
                return left - right
            if isinstance(n.op, ast.Mult):
                return left * right
            # Div
            return left / right

        raise ValueError("Prix invalide")

    return _eval(node)


def parse_price_to_float(price: str) -> float:
    value = (price or "").strip().replace(",", ".")
    if value == "":
        return 0.0
    value = value.replace(" ", "")
    try:
        return float(value)
    except ValueError:
        return float(_eval_arithmetic_expression(value))


def format_price(price: str) -> str:
    """Normalise un prix saisi en texte vers un affichage float."""
    val = parse_price_to_float(price)
    return f"{val:.2f}"


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
    """Ajoute une dépense au format: id,name,date,price,category,description."""

    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    name = name.strip()
    date = date.strip()
    price = price.strip()
    category = category.strip()
    description = description.strip()

    if not name:
        raise ValueError("Le nom est obligatoire")
    if not date:
        raise ValueError("La date est obligatoire")
    if not category:
        raise ValueError("La catégorie est obligatoire")
    try:
        # Validation uniquement: on conserve l'expression pour l'édition.
        _ = parse_price_to_float(price)
    except ValueError as exc:
        raise ValueError("Prix invalide") from exc

    # S'assurer que le fichier est déjà migré (sinon les comparaisons seraient incohérentes)
    migrate_expense_ids(csv_path)

    details = [name, date, price, category, description]
    row = [uuid.uuid4().hex, *details]

    if csv_path.exists() and not allow_duplicates:
        with csv_path.open(mode="r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            for existing in reader:
                if not existing:
                    continue
                # format attendu: [id, name, date, price, category, description]
                if len(existing) >= 6 and existing[1:6] == details:
                    raise DuplicateExpenseError("Cette dépense existe déjà")
                # compat ancien format (au cas où)
                if len(existing) == 5 and existing == details:
                    raise DuplicateExpenseError("Cette dépense existe déjà")

    with csv_path.open(mode="a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(row)


def update_expense(
    csv_path: Path,
    *,
    expense_id: str,
    new: list[str],
    allow_duplicates: bool = False,
) -> None:
    """Met à jour une dépense en remplaçant la ligne identifiée par son id.

    Le format attendu pour new est: [name, date, price, category, description].
    """

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise ValueError("Fichier de dépenses introuvable")

    migrate_expense_ids(csv_path)

    expense_id = (expense_id or "").strip()
    if not expense_id:
        raise ValueError("Id de dépense invalide")

    if len(new) != 5:
        raise ValueError("Format de dépense invalide")

    name = (new[0] or "").strip()
    date = (new[1] or "").strip()
    price = (new[2] or "").strip()
    category = (new[3] or "").strip()
    description = (new[4] or "").strip()

    if not name:
        raise ValueError("Le nom est obligatoire")
    if not date:
        raise ValueError("La date est obligatoire")
    if not category:
        raise ValueError("La catégorie est obligatoire")
    try:
        # Validation uniquement: on conserve l'expression pour l'édition.
        _ = parse_price_to_float(price)
    except ValueError as exc:
        raise ValueError("Prix invalide") from exc

    new_details = [name, date, price, category, description]
    new_row = [expense_id, *new_details]

    with csv_path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        rows = [r for r in reader]

    idx: int | None = None
    for i, r in enumerate(rows):
        if len(r) >= 1 and r[0] == expense_id:
            idx = i
            break
    if idx is None:
        raise ValueError("Dépense introuvable")

    if not allow_duplicates:
        for i, r in enumerate(rows):
            if i == idx:
                continue
            if len(r) >= 6 and r[1:6] == new_details:
                raise DuplicateExpenseError("Cette dépense existe déjà")

    rows[idx] = new_row

    with csv_path.open(mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def delete_expense(csv_path: Path, *, expense_id: str) -> None:
    """Supprime une dépense par son id."""

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise ValueError("Fichier de dépenses introuvable")

    migrate_expense_ids(csv_path)

    expense_id = (expense_id or "").strip()
    if not expense_id:
        raise ValueError("Id de dépense invalide")

    with csv_path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        rows = [r for r in reader]

    kept: list[list[str]] = []
    removed = False
    for r in rows:
        if len(r) >= 1 and r[0] == expense_id and not removed:
            removed = True
            continue
        kept.append(r)

    if not removed:
        raise ValueError("Dépense introuvable")

    with csv_path.open(mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(kept)


def migrate_expense_ids(csv_path: Path) -> None:
    """Assure que chaque dépense possède un id en première colonne.

    Migration auto depuis l'ancien format:
      [name, date, price, category, description]
    vers:
      [id, name, date, price, category, description]
    """

    csv_path = Path(csv_path)
    if not csv_path.exists():
        return

    with csv_path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        rows = [r for r in reader]

    needs_write = False
    seen_ids: set[str] = set()
    new_rows: list[list[str]] = []

    for row in rows:
        if not row:
            continue

        # Déjà au nouveau format
        if len(row) >= 6:
            expense_id = (row[0] or "").strip()
            if not expense_id or expense_id in seen_ids:
                expense_id = uuid.uuid4().hex
                needs_write = True
            seen_ids.add(expense_id)
            new_rows.append([expense_id, row[1], row[2], row[3], row[4], row[5]])
            # Si la ligne avait plus de colonnes, on les ignore.
            if len(row) != 6:
                needs_write = True
            continue

        # Ancien format (5 colonnes)
        if len(row) == 5:
            expense_id = uuid.uuid4().hex
            seen_ids.add(expense_id)
            new_rows.append([expense_id, row[0], row[1], row[2], row[3], row[4]])
            needs_write = True
            continue

        # Format inattendu: on tente de le garder mais en imposant 6 colonnes
        expense_id = uuid.uuid4().hex
        seen_ids.add(expense_id)
        name = (row[0] if len(row) >= 1 else "")
        date = (row[1] if len(row) >= 2 else "")
        price = (row[2] if len(row) >= 3 else "")
        category = (row[3] if len(row) >= 4 else "")
        description = (row[4] if len(row) >= 5 else "")
        new_rows.append([expense_id, name, date, price, category, description])
        needs_write = True

    if not needs_write:
        return

    with csv_path.open(mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(new_rows)
