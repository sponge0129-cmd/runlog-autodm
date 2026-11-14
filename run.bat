@echo off
cd /d E:\runlog\autodm
set PYTHONIOENCODING=utf8
python autodm.py >> log.txt 2>&1
