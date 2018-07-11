#!/usr/bin/env python3

import json,subprocess

with open("env.json") as f:
    env_vars = json.loads(f.read())

