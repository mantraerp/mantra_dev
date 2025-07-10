#!/bin/bash

# GIT_USERNAME="mantraerp"
# GIT_TOKEN="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"
# GIT_REPO="github.com/mantraerp/mantra.git"
# BRANCH="main"
# LOG_FILE="/home/mantra/scripts/mantra_pull.log"

# Check cURL command if available (required), abort if does not exists
type curl >/dev/null 2>&1 || { echo >&2 "Required curl but it's not installed. Aborting."; exit 1; }
echo

# PAYLOAD='{"company_name": "mantra", "password": "secret"}'
PAYLOAD='{"company_name":"mantra"}'
# HEADER='{"Content-Type":"application/json"}'

RESPONSE=`curl -s --request POST -H "Content-Type:application/json" http://192.168.1.38:8001/api/method/mantra_dev.backend_code.gitapi.mantra_git_detail --data "${PAYLOAD}"`

GIT_TOKEN=`echo "$RESPONSE" | jq -r '.message.GIT_TOKEN'`
GIT_USERNAME=`echo "$RESPONSE" | jq -r '.message.GIT_USERNAME'`
GIT_REPO=`echo "$RESPONSE" | jq -r '.message.GIT_REPO'`
GIT_BRANCH=`echo "$RESPONSE" | jq -r '.message.GIT_BRANCH'`
LOG_FILE="/home/mantra/scripts/mantra_pull.log"




#Mefron pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in Mefron" >> "$LOG_FILE" 2>&1
cd '/home/mefron-bench/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in Mefron" >> "$LOG_FILE" 2>&1

#Smart pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in Smart identity" >> "$LOG_FILE" 2>&1
cd '/home/mantrasmartidentity_india/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in Smart identity" >> "$LOG_FILE" 2>&1

#Mitras pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in Mitras globle" >> "$LOG_FILE" 2>&1
cd '/home/mitras_global/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in Mitras globle" >> "$LOG_FILE" 2>&1

#Mewurk pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in Mewurk" >> "$LOG_FILE" 2>&1
cd '/home/mewurk/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in Mewurk" >> "$LOG_FILE" 2>&1

#Mocula pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in Mocula" >> "$LOG_FILE" 2>&1
cd '/home/mocula/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in Mocula" >> "$LOG_FILE" 2>&1

#Mupizo pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in Mupizo" >> "$LOG_FILE" 2>&1
cd '/home/mupizo/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in Mupizo" >> "$LOG_FILE" 2>&1

#Fzco pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in Fzco" >> "$LOG_FILE" 2>&1
cd '/home/fzco/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in Fzco" >> "$LOG_FILE" 2>&1

#fzco dubai pull
echo "$(date '+%FT%H:%M:%S') - Start Mantra pull in fzco dubai" >> "$LOG_FILE" 2>&1
cd '/home/frappe-bench/apps/mantra/'
git reset --hard
git clean -fd
git pull https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - End Mantra pull in fzco dubai" >> "$LOG_FILE" 2>&1