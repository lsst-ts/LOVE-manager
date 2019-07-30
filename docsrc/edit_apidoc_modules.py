"""Edits the apidoc modules.rst file in order to have a better explanation."""
import sys
import fileinput

if __name__ == '__main__':
    for i, line in enumerate(fileinput.input('source/apidoc/modules.rst', inplace=1)):
        if i == 0:
            sys.stdout.write('ApiDoc\n')
        elif i == 1:
            sys.stdout.write('======\n')
        elif i == 2:
            sys.stdout.write('These are the ApiDocs of the project.\n\n')
        else:
            sys.stdout.write(line)
