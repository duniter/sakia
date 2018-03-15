@ECHO ON

call activate test-environment

echo "%PATH%"
echo "%QT_PLUGIN_PATH%"
python -V

lrelease -version

call pyuic5 --version
pyrcc5 -version

pip install -r requirements.txt
pip install pyinstaller==3.2
pip install six
pip install packaging

python gen_resources.py
if %errorlevel% neq 0 exit /b 1s

.\\ci\\appveyor\\gen_translations.cmd
if %errorlevel% neq 0 exit /b 1

pyinstaller sakia.spec
if %errorlevel% neq 0 exit /b 1
