#!/bin/bash

GIT_TOKEN="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"
GIT_USERNAME="mantraerp"
BRANCH="main"
LOG_FILE="/home/mantra/scripts/mantra_push.log"


#Mefron
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push Mefron" >> "$LOG_FILE" 2>&1
cd '/home/mefron-bench/apps/mefron_dev/'
bench export-fixtures --app mefron_dev
truncate /home/mefron-bench/nohup.out --size 0
truncate /home/mefron-bench/apps/mefron_dev/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/Mefron-Dev.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done Mefron" >> "$LOG_FILE" 2>&1


#Smart Identity
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push Smart Identity" >> "$LOG_FILE" 2>&1
cd /home/mantrasmartidentity_india/apps/smart_identity
bench export-fixtures --app smart_identity
truncate /home/mantrasmartidentity_india/nohup.out --size 0
truncate /home/mantrasmartidentity_india/apps/smart_identity/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/smart_identity.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done Smart Identity" >> "$LOG_FILE" 2>&1


#Mitras Globle
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push Mitras Globle" >> "$LOG_FILE" 2>&1
cd /home/mitras_global/apps/mitras_global/
bench export-fixtures --app mitras_global
truncate /home/mitras_global/nohup.out --size 0
truncate /home/mitras_global/apps/mitras_global/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mitras_global.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done Mitras Globle" >> "$LOG_FILE" 2>&1


#Mewurk
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push Mewurk" >> "$LOG_FILE" 2>&1
cd /home/mewurk/apps/mewurk/
bench export-fixtures --app mewurk
truncate /home/mewurk/nohup.out --size 0
truncate /home/mewurk/apps/mewurk/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mewurk.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done Mewurk" >> "$LOG_FILE" 2>&1


#Mocula
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push Mocula" >> "$LOG_FILE" 2>&1
cd /home/mocula/apps/mocula/
bench export-fixtures --app mocula
truncate /home/mocula/nohup.out --size 0
truncate /home/mocula/apps/mocula/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mocula.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done Mocula" >> "$LOG_FILE" 2>&1


#Mupizo
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push Mupizo" >> "$LOG_FILE" 2>&1
cd /home/mupizo/apps/mupizo/
bench export-fixtures --app mupizo
truncate /home/mupizo/nohup.out --size 0
truncate /home/mupizo/apps/mupizo/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/mupizo.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done Mupizo" >> "$LOG_FILE" 2>&1


#FZCO 
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push FZCO" >> "$LOG_FILE" 2>&1
cd /home/fzco/apps/fzco/
bench export-fixtures --app fzco
truncate /home/fzco/nohup.out --size 0
truncate /home/fzco/apps/fzco/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/fzco.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done FZCO" >> "$LOG_FILE" 2>&1


#FZCO Dubai 
DATE2=$(date '+%F_%H:%M:%S')
echo "$DATE2 - Starting push FZCO Dubai" >> "$LOG_FILE" 2>&1
cd /home/frappe-bench/apps/fzco_dubai/
bench export-fixtures --app fzco_dubai
truncate /home/frappe-bench/nohup.out --size 0
truncate /home/frappe-bench/apps/fzco_dubai/nohup.out --size 0
git add .
DATE2=$(date '+%F_%H:%M:%S')
COMMIT_MSG="Auto_commit_$DATE2"
git commit -m "$COMMIT_MSG"
echo "$DATE2 - Commit $COMMIT_MSG" >> "$LOG_FILE"
git rm --cached nohup.out
GIT_REPO="github.com/mantraerp/fzco-dubai.git"
git push https://${GIT_USERNAME}:${GIT_TOKEN}@${GIT_REPO} $BRANCH
DATE3=$(date '+%F_%H:%M:%S')
echo "$DATE3 - Push done FZCO Dubai" >> "$LOG_FILE" 2>&1