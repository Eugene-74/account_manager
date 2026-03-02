from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


__all__ = ["__version__"]


def _extract_version_from_tag(tag: str) -> str:
	tag = (tag or "").strip()
	if not tag:
		return "0.0.0"
	# Ex: "refs/tags/v1.0.0v12" -> "v1.0.0v12"
	if "/" in tag:
		tag = tag.split("/")[-1]
	# On garde la partie majeure.mineure.corrective en priorité.
	# Ex: "v1.0.0v12" -> "v1.0.0"
	match = re.match(r"^(v?\d+\.\d+\.\d+)", tag)
	if match:
		return match.group(1)
	# Fallback: au moins majeur.mineure
	match = re.match(r"^(v?\d+\.\d+)", tag)
	if match:
		return match.group(1)
	return tag


def _detect_version() -> str:
	"""Détermine automatiquement __version__ à partir d'un tag ou d'un fichier.

	Ordre de priorité:
	- variable d'environnement ACCOUNT_MANAGER_TAG
	- variables CI courantes (GITHUB_REF_NAME, GIT_TAG, APP_VERSION)
	- dernier tag Git local (git describe) si disponible
	- fichier resources/version.txt (s'il existe)
	- valeur de secours "0.0.0"
	"""

	tag = os.getenv("ACCOUNT_MANAGER_TAG")
	if not tag:
		tag = (
			os.getenv("GITHUB_REF_NAME")
			or os.getenv("GIT_TAG")
			or os.getenv("APP_VERSION")
		)
	if tag:
		return _extract_version_from_tag(tag)

	# En dev: tenter de récupérer le dernier tag Git du dépôt.
	try:
		repo_root = Path(__file__).resolve().parents[1]
		result = subprocess.run(
			["git", "describe", "--tags", "--abbrev=0"],
			cwd=str(repo_root),
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
			text=True,
			timeout=1.0,
		)
		if result.returncode == 0 and result.stdout.strip():
			return _extract_version_from_tag(result.stdout)
	except (OSError, subprocess.SubprocessError):
		pass

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
