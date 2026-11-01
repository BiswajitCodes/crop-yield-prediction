@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 ( set PYCMD=py -3 ) else ( set PYCMD=python )
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PYCMD% -m venv .venv
  if errorlevel 1 ( echo Could not create venv. Install Python 3.11 or newer from python.org. & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"
fc /b requirements.txt ".venv\req_installed.txt" >nul 2>nul
if errorlevel 1 (
  echo Installing dependencies. This can take a few minutes the first time...
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  if errorlevel 1 ( echo Dependency installation failed. & pause & exit /b 1 )
  copy /y requirements.txt ".venv\req_installed.txt" >nul
)
echo Starting CropYield AI at http://localhost:8501
python -m streamlit run app.py
pause
