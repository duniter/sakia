@ECHO ON

call activate test-environment

echo "%PATH%"
echo "%QT_QPA_PLATFORM_PLUGIN_PATH%"
python -V
call pyuic5 --version

pyrcc5 -version

lrelease -version

pip install -r requirements.txt

python gen_resources.py
if %errorlevel% neq 0 exit /b 1s

python gen_translations.py
if %errorlevel% neq 0 exit /b 1

python setup.py build
if %errorlevel% neq 0 exit /b 1
