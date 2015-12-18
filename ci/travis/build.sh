#!/usr/bin/env bash
eval "$(pyenv virtualenv-init -)"

pyenv activate sakia-env
pip install coveralls cx_Freeze
pip install -r requirements.txt
python gen_resources.py
python gen_translations.py
python setup.py bdist_dmg