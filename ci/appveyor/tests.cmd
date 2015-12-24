@ECHO ON

call activate test-environment

echo "%PATH%"
echo "%QT_QPA_PLATFORM_PLUGIN_PATH%"
python -V
call pyuic5 --version

pyrcc5 -version

lrelease -version

python -m unittest discover --start-directory src/sakia/tests -t src

if %errorlevel% neq 0 exit /b 1