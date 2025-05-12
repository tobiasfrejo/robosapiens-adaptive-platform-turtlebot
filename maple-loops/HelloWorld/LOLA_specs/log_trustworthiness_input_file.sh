#!/bin/bash

SPECFILE="$(realpath "$1")"
SPECBASE="$(basename "$SPECFILE")"
INPUTFILE="$(realpath "$2")"
INPUTBASE="$(basename "$INPUTFILE")"
HOSTDIR="$(dirname "$SPECFILE")"

LOGFILE="Logs/${SPECBASE}_$(date +%Y-%m-%d_%H.%M.%S).txt"

CMD="docker run --network host -it --rm -e RUST_BACKTRACE=full -v $HOSTDIR:/mnt/host_models localhost/trustworthiness-checker /mnt/host_models/$SPECBASE --input-file /mnt/host_models/$INPUTBASE"

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
echo "========         INPUT          ======="
echo "Source: $INPUTBASE"
cat "$INPUTFILE"
echo ""
echo ""
echo "======== TRUSTWORTHINESS OUTPUT ======="
$CMD 2>&1
} | tee -a "$LOGFILE"
