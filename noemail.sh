#!/bin/bash

crontab -l | sed -e "s:agent-updater/control start:agent-updater/control start >/dev/null 2>\&1:" | crontab -

