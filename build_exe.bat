@echo off
setlocal

REM Build a Windows .exe using PyInstaller.
REM Prereq: venv created in accountManagerEnv\env and deps installed.

call accountManagerEnv\env\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Build a single .exe directly in dist
pyinstaller --noconfirm --clean --onefile --noconsole ^
  --name AccountManager ^
  --icon resources\app.ico ^
  --add-data "resources\app.ico;resources" ^
  run_app.py

echo.
echo Build done: dist\AccountManager.exe
endlocal
