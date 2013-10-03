#!/bin/bash

ENVIRONMENTS_PATH="./it-puppet-environments"
ENVIRONMENTS_GIT_URL="http://git.cern.ch/cernpub/it-puppet-environments"
LOG_DIR="./log"

[[ -d $LOG_DIR ]] || mkdir $LOG_DIR
LOG_FILE="$LOG_DIR/ai-environments-reminder.log"
echo "START: $(date)" >> $LOG_FILE

[[ ! -d $ENVIRONMENTS_PATH ]] && git clone -b master $ENVIRONMENTS_GIT_URL \
  $ENVIRONMENTS_PATH &>> $LOG_FILE

GIT_WORK_TREE="$ENVIRONMENTS_PATH" GIT_DIR="$ENVIRONMENTS_PATH/.git" git fetch \
  origin &>> $LOG_FILE
GIT_WORK_TREE="$ENVIRONMENTS_PATH" GIT_DIR="$ENVIRONMENTS_PATH/.git" git merge \
  origin/master &>> $LOG_FILE

python ai-environments-reminder.py -e $ENVIRONMENTS_PATH &>> $LOG_FILE
echo "END: $(date)" >> $LOG_FILE
