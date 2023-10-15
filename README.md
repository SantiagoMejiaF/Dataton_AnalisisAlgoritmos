# dataton2023-Post-Data
Repositorio del equipo Post-Data para la competencia de Dataton de Bancolombia

## Installation

After the installation of python 3.11 run the batch file "install.bat" who already has the virtual Enviroment installation and all their dependencys listed in "requirements.txt" wich can be extendend if needed.

To add a new package to the project it is possible to just update the list and re-run the installation batch file.

Batch file content and commands is as follows:
```bash
	@echo off
		python.exe -m venv virtualEnviroment
		call virtualEnviroment\Scripts\activate.bat
		python.exe -m pip install --upgrade pip
		python.exe -m pip install -r .\src\requirements.txt
		start run.bat
```
## Run Locally

Starting the server with the batch file "run.bat" will just call the virtual Enviroment and then call main.py.

To start the server manually just introduce the command executed in the project folder:

```bash
    virtualEnviroment\Scripts\activate.bat
    python main.py
```

The Batch file content and commands are as follows:
```bash
	@echo off
		call virtualEnviroment\Scripts\activate.bat
		python main.py
```