#!/bin/bash

# GIT_TOKEN="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"
# GIT_USERNAME="mantraerp"
# BRANCH="main"
# LOG_FILE="/home/mantra/scripts/mantra_push.log"


# Check cURL command if available (required), abort if does not exists
type curl >/dev/null 2>&1 || { echo >&2 "Required curl but it's not installed. Aborting."; exit 1; }
echo

PAYLOAD='{"company_name":"mantra"}'
RESPONSE=`curl -s --request POST -H "Content-Type:application/json" http://192.168.1.38:8001/api/method/mantra_dev.backend_code.gitapi.mantra_git_detail --data "${PAYLOAD}"`

GIT_TOKEN=`echo "$RESPONSE" | jq -r '.message.GIT_TOKEN'`
GIT_USERNAME=`echo "$RESPONSE" | jq -r '.message.GIT_USERNAME'`
GIT_BRANCH=`echo "$RESPONSE" | jq -r '.message.GIT_BRANCH'`
LOG_FILE="/home/mantra/scripts/mantra_push.log"


#Mefron
echo "$(date '+%FT%H:%M:%S') - Starting push Mefron" >> "$LOG_FILE" 2>&1
cd '/home/mefron-bench/apps/mefron_dev/'
bench export-fixtures --app mefron_dev
truncate /home/mefron-bench/nohup.out --size 0
truncate /home/mefron-bench/apps/mefron_dev/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/Mefron-Dev.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done Mefron" >> "$LOG_FILE" 2>&1

#Smart Identity
echo "$(date '+%FT%H:%M:%S') - Starting push Smart Identity" >> "$LOG_FILE" 2>&1
cd /home/mantrasmartidentity_india/apps/smart_identity
bench export-fixtures --app smart_identity
truncate /home/mantrasmartidentity_india/nohup.out --size 0
truncate /home/mantrasmartidentity_india/apps/smart_identity/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/smart_identity.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done Smart Identity" >> "$LOG_FILE" 2>&1

#Mitras Globle
echo "$(date '+%FT%H:%M:%S') - Starting push Mitras Globle" >> "$LOG_FILE" 2>&1
cd /home/mitras_global/apps/mitras_global/
bench export-fixtures --app mitras_global
truncate /home/mitras_global/nohup.out --size 0
truncate /home/mitras_global/apps/mitras_global/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mitras_global.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done Mitras Globle" >> "$LOG_FILE" 2>&1

#Mewurk
echo "$(date '+%FT%H:%M:%S') - Starting push Mewurk" >> "$LOG_FILE" 2>&1
cd /home/mewurk/apps/mewurk/
bench export-fixtures --app mewurk
truncate /home/mewurk/nohup.out --size 0
truncate /home/mewurk/apps/mewurk/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mewurk.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done Mewurk" >> "$LOG_FILE" 2>&1

#Mocula
echo "$(date '+%FT%H:%M:%S') - Starting push Mocula" >> "$LOG_FILE" 2>&1
cd /home/mocula/apps/mocula/
bench export-fixtures --app mocula
truncate /home/mocula/nohup.out --size 0
truncate /home/mocula/apps/mocula/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mocula.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done Mocula" >> "$LOG_FILE" 2>&1

#Mupizo
echo "$(date '+%FT%H:%M:%S') - Starting push Mupizo" >> "$LOG_FILE" 2>&1
cd /home/mupizo/apps/mupizo/
bench export-fixtures --app mupizo
truncate /home/mupizo/nohup.out --size 0
truncate /home/mupizo/apps/mupizo/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mupizo.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done Mupizo" >> "$LOG_FILE" 2>&1


#FZCO 
echo "$(date '+%FT%H:%M:%S') - Starting push FZCO" >> "$LOG_FILE" 2>&1
cd /home/fzco/apps/fzco/
bench export-fixtures --app fzco
truncate /home/fzco/nohup.out --size 0
truncate /home/fzco/apps/fzco/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/fzco.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done FZCO" >> "$LOG_FILE" 2>&1


#FZCO Dubai 
echo "$(date '+%FT%H:%M:%S') - Starting push FZCO Dubai" >> "$LOG_FILE" 2>&1
cd /home/frappe-bench/apps/fzco_dubai/
bench export-fixtures --app fzco_dubai
truncate /home/frappe-bench/nohup.out --size 0
truncate /home/frappe-bench/apps/fzco_dubai/nohup.out --size 0
git add .
COMMIT_MSG="AC_$(date '+%FT%H:%M:%S')"
git commit -m "$COMMIT_MSG"
echo "$(date '+%FT%H:%M:%S') - $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/fzco-dubai.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
echo "$(date '+%FT%H:%M:%S') - Push done FZCO Dubai" >> "$LOG_FILE" 2>&1