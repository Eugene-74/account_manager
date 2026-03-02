import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


GITHUB_API_LATEST_RELEASE = "https://api.github.com/repos/{owner}/{repo}/releases/latest"


class GitHubUpdateError(Exception):
    """Custom exception for GitHub update related errors."""


def get_latest_version_from_github(owner: str, repo: str) -> str:
    """Return the latest release tag name for a given GitHub repository.

    This uses the public GitHub API and does not require authentication,
    but is subject to GitHub's anonymous rate limits.
    """

    url = GITHUB_API_LATEST_RELEASE.format(owner=owner, repo=repo)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "account-manager-updater"},
    )

    try:
        with urllib.request.urlopen(request) as response:  # type: ignore[arg-type]
            if response.status != 200:
                raise GitHubUpdateError(f"GitHub API returned status {response.status}")

            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        raise GitHubUpdateError(f"HTTP error while querying GitHub: {exc}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise GitHubUpdateError(f"Network error while querying GitHub: {exc}") from exc
    except OSError as exc:
        raise GitHubUpdateError(f"OS error while querying GitHub: {exc}") from exc

    tag_name = data.get("tag_name")
    if not isinstance(tag_name, str):
        raise GitHubUpdateError("Invalid response from GitHub: missing tag_name")

    return tag_name


def _select_asset(data: Dict[str, Any], asset_name_substring: Optional[str]) -> Dict[str, Any]:
    assets = data.get("assets") or []
    if not isinstance(assets, list):
        raise GitHubUpdateError("Invalid response from GitHub: assets is not a list")

    selected: Optional[Dict[str, Any]] = None

    if asset_name_substring:
        for asset in assets:
            name = asset.get("name")
            if isinstance(name, str) and asset_name_substring in name:
                selected = asset
                break

    if selected is None:
        for asset in assets:
            name = asset.get("name")
            if isinstance(name, str) and name.lower().endswith((".exe", ".msi", ".zip")):
                selected = asset
                break

    if selected is None:
        raise GitHubUpdateError("No suitable asset found in the latest GitHub release")

    return selected


def install_latest_version_from_github(
    owner: str,
    repo: str,
    asset_name_substring: Optional[str] = None,
    download_dir: Optional[str] = None,
    launch_installer: bool = True,
) -> str:
    """Download (and optionally launch) the latest installer from GitHub releases.

    Parameters
    ----------
    owner: str
        GitHub user or organisation name.
    repo: str
        Repository name.
    asset_name_substring: Optional[str]
        If provided, the first asset whose name contains this substring is chosen.
        Otherwise, the first asset ending with .exe, .msi or .zip is used.
    download_dir: Optional[str]
        Directory where the downloaded file will be stored. If None, a temporary
        directory is used.
    launch_installer: bool
        If True and running on Windows, the downloaded file is opened with the
        default handler (typically starting the installer).

    Returns
    -------
    str
        The full path of the downloaded asset.
    """

    url = GITHUB_API_LATEST_RELEASE.format(owner=owner, repo=repo)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "account-manager-updater"},
    )

    try:
        with urllib.request.urlopen(request) as response:  # type: ignore[arg-type]
            if response.status != 200:
                raise GitHubUpdateError(f"GitHub API returned status {response.status}")

            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        raise GitHubUpdateError(f"HTTP error while querying GitHub: {exc}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise GitHubUpdateError(f"Network error while querying GitHub: {exc}") from exc
    except OSError as exc:
        raise GitHubUpdateError(f"OS error while querying GitHub: {exc}") from exc

    asset = _select_asset(data, asset_name_substring)

    download_url = asset.get("browser_download_url")
    name = asset.get("name")

    if not isinstance(download_url, str) or not isinstance(name, str):
        raise GitHubUpdateError("Invalid asset data from GitHub: missing name or URL")

    if download_dir is None:
        download_dir = tempfile.gettempdir()

    os.makedirs(download_dir, exist_ok=True)
    target_path = os.path.join(download_dir, name)

    try:
        with urllib.request.urlopen(download_url) as response:  # type: ignore[arg-type]
            if response.status not in (200, 302):
                raise GitHubUpdateError(
                    f"Failed to download asset, HTTP status {response.status}"
                )
            with open(target_path, "wb") as fh:
                chunk = response.read(8192)
                while chunk:
                    fh.write(chunk)
                    chunk = response.read(8192)
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        raise GitHubUpdateError(f"HTTP error while downloading asset: {exc}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise GitHubUpdateError(f"Network error while downloading asset: {exc}") from exc
    except OSError as exc:
        raise GitHubUpdateError(f"OS error while downloading asset: {exc}") from exc

    if launch_installer and sys.platform.startswith("win"):
        try:
            os.startfile(target_path)  # type: ignore[attr-defined]
        except OSError as exc:
            raise GitHubUpdateError(f"Failed to launch installer: {exc}") from exc

    return target_path
