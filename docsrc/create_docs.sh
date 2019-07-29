#!/bin/bash
rm -rf source/apidoc
sphinx-apidoc -o source/apidoc ../manager ../manager/*migrations*
python edit_apidoc_modules.py
rm -rf ../docs/doctrees
rm -rf ../docs/html
make html
