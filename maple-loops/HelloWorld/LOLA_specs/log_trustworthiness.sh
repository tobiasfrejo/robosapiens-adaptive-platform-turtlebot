#!/bin/bash

SPECFILE="$(realpath "$1")"
SPECBASE="$(basename "$SPECFILE")"
HOSTDIR="$(dirname "$SPECFILE")"

LOGFILE="Logs/${SPECBASE}_$(date +%Y-%m-%d_%H.%M.%S).txt"

IN_TOPICS="$(awk -F'[: ]+' '/^in/{for (i=2; i<=NF-1; i++) printf "%s ", $i}' $SPECFILE | sed 's/ *$//')"
OUT_TOPICS="$(awk -F'[: ]+' '/^out/{for (i=2; i<=NF-1; i++) printf "%s ", $i}' $SPECFILE | sed 's/ *$//')"

CMD="docker run --network host -it --rm -e RUST_BACKTRACE=full -v $HOSTDIR:/mnt/host_models localhost/trustworthiness-checker:latest /mnt/host_models/$SPECBASE --input-mqtt-topics stage"

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
