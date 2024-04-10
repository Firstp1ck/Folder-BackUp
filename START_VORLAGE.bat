@echo off
:: Überprüfen, ob das Paket 'python-docx' bereits installiert ist
python -m pip list | findstr /C:"python-docx" > nul

:: Wenn das Paket nicht gefunden wurde, führe die Installation aus
if errorlevel 1 (
    echo Pakete werden installiert...

    python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org 

) else (
    echo Paket sind bereits installiert.
)

:: Führen Sie Ihr Python-Skript aus. Ersetzen Sie 'app.py' durch den Namen Ihres Skripts.
python backup_firmenordner.py

echo.
echo Skript wurde ausgeführt. Fenster schließen oder weitere Befehle eingeben.
pause

