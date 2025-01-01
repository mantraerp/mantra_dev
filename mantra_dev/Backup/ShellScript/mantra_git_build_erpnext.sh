#!/bin/bash

time_stamp=$(date +%Y-%m-%d-%T)
echo "Bench build erpnext $time_stamp" >> /home/mantra/mantrastage-bench/logs/gitauto.log 2>&1
cd /home/mantra/mantrastage-bench/
bench build --app erpnext
