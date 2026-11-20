#!/bin/bash
# Construct probe: main run (112 prompts), then the persona positive control (40 prompts).
cd "$(dirname "$0")/.."
PY=.venv/bin/python
$PY pilot/construct_probe.py > pilot/out/construct_probe.log 2>&1
PERSONA=1 $PY pilot/construct_probe.py > pilot/out/construct_probe_persona.log 2>&1
