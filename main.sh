#!/bin/bash

python3 src/main.py testing

cd public && python3 -m http.server 8888