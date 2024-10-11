#!/bin/bash
cd /root/.project/
eval "$(ssh-agent -s)"
ssh-add /root/.ssh/project
git reset --hard HEAD
git pull git@github.com:Foldren/stats_bot.git

