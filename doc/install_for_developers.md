# Install Sakia for developpers
### Windows install

 * Download and install [vcredist2015](https://www.microsoft.com/fr-FR/download/details.aspx?id=48145)
 * Download and install [Miniconda](http://conda.pydata.org/miniconda.html).
 * Download and install [Git](https://git-scm.com/) and add the binaries path to your `PATH` variable
 * Download and install [Qt 5.6](http://download.qt.io/development_releases/qt/5.6/) for your architecture (msvc2015_64 for 64 bits, msvc2015 for 32 bits)
 * Open Conda console then : `conda update --yes conda`
 * Restart Conda console then : 

```
conda config --add channels inso/channel/sakia
conda create -n sakia-env python=3.5 pyqt5 libsodium=1.0.3
activate sakia-env
pip install -r requirements.txt
pip install pyinstaller
```
 * To run sakia, you have to export the following variable in your conda console : 

```
SET PYTHONPATH=[Path to sakia dir]\\src;%PYTHONPATH%
```

 * Then : 
```batch
python gen_resources.py 
python gen_translations.py
python src/sakia/main.py
```

### Linux & Macos (Pyenv install)
#### Linux System dependencies
##### Fedora
    sudo dnf install libsodium qt5-qtsvg python3-qt5 qt5-qttools \
    qt5-qttools-devel python3-qt5-devel qtchooser openssl-devel zfstream-devel \
    readline-devel sqlite-devel gcc-c++ \
    qt5-qtbase-devel qt5-qtsvg-devel

    sudo ln -s /usr/bin/lrelease-qt5 /usr/bin/lrelease

##### Ubuntu 14.04+ install

    sudo apt-get install curl qt5-qmake qtbase5-dev qttools5-dev-tools libqt5svg5-dev libdbus-1-dev libdbus-glib-1-dev autoconf automake libtool

64 bits:

      wget http://archive.ubuntu.com/ubuntu/pool/universe/libs/libsodium/libsodium13_1.0.1-1_amd64.deb
      sudo dpkg -i libsodium13_1.0.1-1_amd64.deb

32 bits:

     wget http://archive.ubuntu.com/ubuntu/pool/universe/libs/libsodium/libsodium13_1.0.1-1_i386.deb
     sudo dpkg -i libsodium13_1.0.1-1_i386.deb

##### Install pyenv on your home:

* Linux : 
```bash
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
```

Add in `~/.bash_profile`, in `~/.bashrc` on Fedora:
```bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv virtualenv-init -)"
eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"
```
Restart your terminal.


#### MacOS system dependencies

Install the following brew packages : 
```bash
brew install wget
brew install libsodium
## Ensure your brew QT version is up to date. (brew install qt -> qt 4.8)
brew install qt5
brew link --force qt5
## Install pyenv
brew install pyenv
brew install pyenv-virtualenv
```

After installation, you'll need to add :  
```bash
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
to your profile (as stated in the caveats displayed by Homebrew — to display them again, use brew info pyenv). You only need to add that to your profile once.

If you are running El Capitan (MacOS 10.10), you'll need to run `xcode-select --install`

#### Pyenv environment 

##### Build python 3.5.3

Building python 3.5.3 requires libraries of `openssl` and `sqlite3`. On Ubuntu, install it using the following commands : 

```
apt-get update
apt-get install libssl-dev
apt-get install libsqlite3-dev
```

Restart your shell then prepare your virtualenv: 

On GNU/Linux: `PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.5.3`  
On MacOS: `env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.5.3`

Run:
```bash
pyenv shell 3.5.3
pyenv virtualenv sakia-env
```

#### Build Sakia: 

##### Download Sakia

    git clone https://github.com/duniter/sakia

##### Go to dev branch
```bash
cd sakia && git checkout dev
```

##### Configure your PYTHONPATH environment variable
```bash
export PYTHONPATH=${PYTHONPATH}:/YOUR_SAKIA_INSTALL_PATH/src
```

On Linux, you'll need buildable python-dbus and notify2 :  
```bash
pyenv local sakia-env
pip install PyQt5
pip install -U git+https://github.com/posborne/dbus-python.git
pip install notify2
```

To build sakia dependencies, go in sakia directory then : 
```bash
pip install -r requirements.txt --upgrade
pip install pyinstaller
pyenv rehash
```

##### Run Sakia ressources generator

    python gen_resources.py 

##### Run Sakia translations generator

    python gen_translations.py

##### Build Sakia as a binary
```sh
pyinstaller sakia.spec
```

##### Run Sakia build
```sh
./dist/sakia/sakia
```

##### Run Sakia from sources

    cd src && python sakia/main.py


#### Tips
You could find cache repositories on Unix at `~/.conf/sakia` and on Windows at `%APPDATA%\sakia`.

