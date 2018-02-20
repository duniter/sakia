#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os, multiprocessing, subprocess


root_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
resources = os.path.abspath(os.path.join(os.path.dirname(__file__), 'res'))
gen_resources = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src/sakia'))

def convert_ui(args, **kwargs):
    subprocess.call(args, **kwargs)

def build_resources():
    try:
        to_process = []
        for root, dirs, files in os.walk(root_path):
            for f in files:
                if f.endswith('.ui'):
                    source = os.path.join(root, f)
                    dest = os.path.join(root, os.path.splitext(os.path.basename(source))[0]+'_uic.py')

                    exe = 'pyuic5'
                elif f.endswith('.qrc'):
                    source = os.path.join(root, f)
                    filename = os.path.splitext(os.path.basename(source))[0]
                    # we remove "sakia." from the rc filename
                    # its only named like this so that imports are corrects in uic files
                    dest = os.path.join(gen_resources, filename.replace('sakia.', '')+'_rc.py')
                    exe = 'pyrcc5'
                else:
                    continue
                print(source + " >> " + dest)
                to_process.append([exe, '-o', dest, source])

        if sys.platform.startswith('win'):
            # doing this in parallel on windows will crash your computer
            [convert_ui(args, shell=True) for args in to_process]
        else:
            pool = multiprocessing.Pool()
            pool.map(convert_ui, to_process)
    except EnvironmentError:
        print("""\
Warning: PyQt5 development utilities (pyuic5 and pyrcc5) not found
Unable to install praxes' graphical user interface
""")

build_resources()