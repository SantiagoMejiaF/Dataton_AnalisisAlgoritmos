@echo off
python.exe -m venv virtualEnviroment
call virtualEnviroment\Scripts\activate.bat
python.exe -m pip install --upgrade pip
python.exe -m pip install -r .\src\requirements.txt
start run.bat