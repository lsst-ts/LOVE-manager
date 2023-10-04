#!/bin/bash
rm -rf source/apidoc
sphinx-apidoc -o source/apidoc ../manager ../manager/*migrations*
python edit_apidoc_modules.py
