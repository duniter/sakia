@ECHO ON

call activate test-environment

echo "%PATH%"
echo "%QT_PLUGIN_PATH%"
python -V
call pyuic5 --version

pyrcc5 -version

lrelease -version

pip install -r requirements.txt
pip install pyinstaller

python gen_resources.py
if %errorlevel% neq 0 exit /b 1s

python gen_translations.py
if %errorlevel% neq 0 exit /b 1

pyinstaller sakia.spec
if %errorlevel% neq 0 exit /b 1
