from __future__ import annotations

import importlib.metadata
import re
import tomllib
from pathlib import Path


__all__ = ["__version__"]


def _extract_version_from_tag(tag: str) -> str:
	tag = (tag or "").strip()
	if not tag:
		return "0.0.0"
	# Ex: "refs/tags/v1.0.0" -> "v1.0.0"
	if "/" in tag:
		tag = tag.split("/")[-1]
	# On garde la partie majeure.mineure.corrective en priorité.
	match = re.match(r"^(v?\d+\.\d+\.\d+)", tag)
	if match:
		return match.group(1)
	# Fallback: au moins majeur.mineure
	match = re.match(r"^(v?\d+\.\d+)", tag)
	if match:
		return match.group(1)
	return tag


def _read_version_from_pyproject() -> str | None:
	try:
		repo_root = Path(__file__).resolve().parents[1]
		pyproject_path = repo_root / "pyproject.toml"
		if not pyproject_path.is_file():
			return None

		data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
		project = data.get("project")
		if not isinstance(project, dict):
			return None
		version = project.get("version")
		if not isinstance(version, str):
			return None

		clean = version.strip()
		return clean or None
	except Exception:
		return None


def _detect_version() -> str:
	"""Détermine automatiquement __version__ depuis pyproject.toml.

	Ordre de priorité:
	- métadonnées installées du package (issues du pyproject)
	- pyproject.toml (source du dépôt)
	- fichier resources/version.txt (s'il existe)
	- valeur de secours "0.0.0"
	"""

	try:
		installed = importlib.metadata.version("account-manager")
		if installed and installed.strip():
			return _extract_version_from_tag(installed)
	except importlib.metadata.PackageNotFoundError:
		pass
	except Exception:
		pass

	pyproject_version = _read_version_from_pyproject()
	if pyproject_version:
		return _extract_version_from_tag(pyproject_version)

	# Option: fichier texte embarqué contenant le tag ou la version
	try:
		here = Path(__file__).resolve().parent
		version_file = here.parent / "resources" / "version.txt"
		if version_file.is_file():
			content = version_file.read_text(encoding="utf-8")
			return _extract_version_from_tag(content)
	except OSError:
		pass

	return "0.0.0"


__version__ = _detect_version()
