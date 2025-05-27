@echo off
REM Create virtual environment
python -m venv .venv

REM Activate virtual environment
call .venv\Scripts\activate

REM Upgrade pip (optional but recommended)
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt

echo.
echo Setup complete. Virtual environment is ready and dependencies installed.
pause