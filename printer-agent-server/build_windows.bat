@echo off
setlocal enabledelayedexpansion

echo ============================
echo Installing dependencies...
echo ============================

pip install -r requirements.txt

echo ============================
echo Building with Nuitka (onefile)...
echo ============================

python -m nuitka ^
  --standalone ^
  --onefile ^
  --assume-yes-for-downloads ^
  --include-package=fastapi ^
  --include-package=uvicorn ^
  --include-package=pydantic ^
  --include-package=jinja2 ^
  --include-data-dir=templates=templates ^
  --include-data-file=libusb\libusb-1.0_x32.dll=libusb\libusb-1.0_x32.dll ^
  --include-data-file=libusb\libusb-1.0_x64.dll=libusb\libusb-1.0_x64.dll ^
  main.py

echo ============================
echo ✅ DONE! Output in: main.exe
echo ============================

pause

