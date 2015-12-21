import sys, os, multiprocessing, subprocess, time

src = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'sakia'))
res = os.path.abspath(os.path.join(os.path.dirname(__file__), 'res'))
pro_file_template = """
FORMS = {0}
SOURCES = {1}
TRANSLATIONS = {2}
"""

def generate_pro():
    sources = []
    forms = []
    translations = []
    project_filename = os.path.abspath(os.path.join(
                                        os.path.dirname(__file__),
                                        "sakia-ts-{0}".format(int(time.time()))))
    for root, dirs, files in os.walk(src):
        for f in files:
            if f.endswith('.py') and not f.endswith('_uic.py'):
                sources.append(os.path.join(root, f))
            else:
                continue
            print(os.path.join(root, f))

    for root, dirs, files in os.walk(res):
        for f in files:
            if f.endswith('.ui'):
                forms.append(os.path.join(root, f))
            elif f.endswith('.ts'):
                translations.append(os.path.join(root, f))
            else:
                continue
            print(os.path.join(root, f))

    with open(project_filename, 'w') as outfile:
        outfile.write(pro_file_template.format(""" \\
""".join(forms),
                                               """ \\
""".join(sources),
                                               """ \\
""".join(translations)))
    return project_filename

pro_file = generate_pro()
try:
    if "-noobsolete" in sys.argv:
        print("Removing obsolete strings...")
        subprocess.call(["pylupdate5", "-noobsolete", pro_file])
    else:
        subprocess.call(["pylupdate5", pro_file])
finally:
    os.remove(pro_file)
