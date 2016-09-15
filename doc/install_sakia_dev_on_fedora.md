# Install Sakia dev on Fedora

## Install Sakia
### Clone respository
```bash
mkdir -p ~/projects
git clone -b dev git@gihub.com:/duniter/sakia.git ~/projects/sakia_dev
cd ~/projects/sakia_dev
```

### Install pip dependencies
```bash
sudo pip3 install --upgrade pip
sudo pip3 install -r requirements.txt
```

### Fix Qt link
```bash
sudo ln -s /usr/bin/lrelease-qt5 /usr/bin/lrelease
```

### Script to launch Sakia
```bash
cd ..
echo "#!/bin/bash

if [ $1 == "dev" ]; then
        cd sakia_dev
        git pull
        python3 gen_resources.py
        python3 gen_translations.py
        python3 src/sakia/main.py -d
fi
if [ $1 == "stable" ]; then
        ./sakia_stable/dist/sakia/sakia -d
fi" >> run_sakia.sh
```

## Python path
### Bash
```bash
echo "# Sakia
export PYTHONPATH=/home/$USER/projects/sakia/src" >> ~/.bashrc
```

### Fish
```bash
echo "# Sakia
set -x PYTHONPATH /home/$USER/projects/sakia/src" >> ~/.config/fish/config.fish
```

## Install dependencies
```bash
sudo dnf install -y python3-qt5 python3-jsonschema qt5-qttools-devel python3-qt5-devel libsodium
```

## Launch Sakia
```bash
./run_sakia.sh dev
```

## Upgrade DuniterPy
```bash
sudo pip3 install --upgrade duniterpy
```

## Dependency to build
```bash
sudo pip3 install pyinstaller
```

### Previous dependencies no more needed
```bash
#qtchooser qt5-qtbase-devel qt5-qtsvg-devel openssl-devel \
#zfstream-devel readline-devel sqlite-devel gcc-c++ qt5-qtsvg
```
