#!/bin/sh

# echo now in human format 
date +"%H:%M:%S %m/%d/%Y"

# echo now in timestamp format
date -d "$(date +"%H:%M:%S %m/%d/%Y")" +"%s"
