@ECHO ON

# Add qt to path
SET PATH=%QTDIR%\\bin;%QTDIR%\\lib;%PATH%

lrelease -version

python gen_translations.py
if %errorlevel% neq 0 exit /b 1
