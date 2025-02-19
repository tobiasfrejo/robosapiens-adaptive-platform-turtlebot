#!/bin/bash

SPECFILE="$(realpath "$1")"
SPECBASE="$(basename "$SPECFILE")"
HOSTDIR="$(dirname "$SPECFILE")"

LOGFILE="trustworthiness_$(date +%Y-%m-%d_%H.%M.%S).txt"

CMD="docker run --network host -it --rm -v $HOSTDIR:/mnt/host_models thomasdwright/trustworthiness-checker:latest /mnt/host_models/$SPECBASE --input-mqtt-topics stage"

echo "Saving output to: $LOGFILE"
echo ""

{
echo "Command: $CMD"
echo ""
echo "========     SPECIFICATION      ======="
echo "Source: $SPECBASE"
cat "$SPECFILE"
echo ""
echo ""
echo "======== TRUSTWORTHINESS OUTPUT ======="
$CMD 2>&1
} | tee -a "$LOGFILE"
