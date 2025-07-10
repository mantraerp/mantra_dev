#!/bin/bash

# GIT_TOKEN="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"
# GIT_USERNAME="mantraerp"
# GIT_REPO="github.com/mantraerp/mantra_dev.git"
# BRANCH="main"
# LOG_FILE="/home/mantra/scripts/mantra_push.log"

# Check cURL command if available (required), abort if does not exists
type curl >/dev/null 2>&1 || { echo >&2 "Required curl but it's not installed. Aborting."; exit 1; }
echo

# PAYLOAD='{"company_name": "mantra", "password": "secret"}'
PAYLOAD='{"company_name":"mantra_dev"}'
# HEADER='{"Content-Type":"application/json"}'

RESPONSE=`curl -s --request POST -H "Content-Type:application/json" http://192.168.1.38:8001/api/method/mantra_dev.backend_code.gitapi.mantra_git_detail --data "${PAYLOAD}"`

GIT_TOKEN=`echo "$RESPONSE" | jq -r '.message.GIT_TOKEN'`
GIT_USERNAME=`echo "$RESPONSE" | jq -r '.message.GIT_USERNAME'`
GIT_REPO=`echo "$RESPONSE" | jq -r '.message.GIT_REPO'`
GIT_BRANCH=`echo "$RESPONSE" | jq -r '.message.GIT_BRANCH'`
LOG_FILE="/home/mantra/scripts/mantra_push.log"


#Mantra Dev
echo "$(date '+%FT%H:%M:%S') - Starting push Mantra Dev" >> "$LOG_FILE" 2>&1
cd /home/mantra/mantrastage-bench/apps/mantra_dev/
bench export-fixtures --app mantra_dev
truncate /home/mantra/mantrastage-bench/nohup.out --size 0
truncate /home/mantra/mantrastage-bench/apps/mantra_dev/nohup.out --size 0
git add .
git commit -m "AC-$(date '+%FT%H:%M:%S')"
echo "$(date '+%FT%H:%M:%S') - AC-$(date '+%FT%H:%M:%S')" >> "$LOG_FILE"
git rm --cached nohup.out
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done Mantra Dev" >> "$LOG_FILE" 2>&1
bench clear-cache
bench clear-website-cache
yarn cache clean
pip cache purge
echo "$(date '+%FT%H:%M:%S') - Bench cache clear" >> "$LOG_FILE" 2>&1