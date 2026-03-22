# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


# S'assurer que le dossier du projet est dans sys.path pour pouvoir importer le package.
# En CI avec certaines versions de PyInstaller, __file__ peut ne pas exister.
_spec_path = globals().get("__file__") or globals().get("SPEC") or "AccountManager.spec"
PROJECT_ROOT = Path(_spec_path).resolve().parent if str(_spec_path).strip() else Path.cwd()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


try:
    import src as account_manager  # src/__init__.py fournit __version__
    APP_VERSION = getattr(account_manager, "__version__", "0.0.0") or "0.0.0"
except Exception:
    APP_VERSION = "0.0.0"


# Génère resources/version.txt pour que l'app packagée connaisse sa version.
version_file = PROJECT_ROOT / "resources" / "version.txt"
try:
    version_file.write_text(str(APP_VERSION), encoding="utf-8")
except OSError:
    # En cas d'échec, l'app retombera sur 0.0.0.
    pass


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources\\app.ico', 'resources'),
        ('resources\\version.txt', 'resources'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AccountManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\app.ico'],
)
