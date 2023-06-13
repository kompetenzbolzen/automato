#!/bin/bash

test -d venv && rm -Rf venv/
/usr/bin/env python3 -m virtualenv ./venv/
source ./venv/bin/activate
pip install --editable .
