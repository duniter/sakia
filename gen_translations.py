import sys, os, multiprocessing, subprocess, time, shutil

gen_resources = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src/sakia'))
ts = os.path.abspath(os.path.join(os.path.dirname(__file__), 'res', 'i18n', 'ts'))
qm = os.path.abspath(os.path.join(os.path.dirname(__file__), 'res', 'i18n', 'qm'))
if not os.path.exists(qm):
    os.mkdir(qm)

translations = []
qm_files = []
qm_shortnames = []


def prepare_qm():
    for root, dirs, files in os.walk(ts):
        for f in files:
            if f.endswith('.ts'):
                tsfilename = os.path.join(root, f)
                qmshort = "{0}qm".format(f[:-2])
                qmfilename = os.path.join(qm, qmshort)
                srcdest = (tsfilename, qmfilename)
                translations.append(srcdest)
                qm_shortnames.append(qmshort)
            else:
                continue
            print(os.path.join(root, f))

    for (ts_file, qm_file) in translations:
        # avoid conflict with qt4 lrelease by running qtchooser directly
        if sys.platform.startswith('win') or shutil.which("qtchooser") == None or "--lrelease" in sys.argv:
            subprocess.call(["lrelease", ts_file, "-qm", qm_file])
        else:
            subprocess.call(["qtchooser", "-run-tool=lrelease", "-qt=5", ts_file, "-qm", qm_file])
        print(ts_file + " >> " + qm_file)


def build_resources():
    files = ""
    for file in qm_shortnames:
        files += """
<file alias="{0}">qm/{0}.qm</file>""".format(file[:-3])
    rccfile = """<RCC>
      <qresource prefix="i18n">{0}
      </qresource>
    </RCC>
    """.format(files)
    print(rccfile)

    qrc_filename = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                'res',
                                                'i18n',
                                                'langs-{0}.qrc'.format(int(time.time()))
                                                ))

    pyc_filename = os.path.abspath(os.path.join(gen_resources, 'i18n_rc.py'))
    with open(qrc_filename, 'w') as outfile:
        outfile.write(rccfile)

    try:
        subprocess.call(["pyrcc5", "-o", pyc_filename, qrc_filename])
        print(qrc_filename + " >> " + pyc_filename)
    finally:
        os.remove(qrc_filename)


prepare_qm()
build_resources()
