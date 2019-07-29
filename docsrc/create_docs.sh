#!/bin/bash
rm -rf apidoc
sphinx-apidoc -o source/apidoc ../manager
rm -rf ../docs/doctrees
rm -rf ../docs/html
make html
