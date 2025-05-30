#!/bin/bash

SPECFILE="$(realpath "$1")"
SPECBASE="$(basename "$SPECFILE")"
HOSTDIR="$(dirname "$SPECFILE")"

LOGFILE="Logs/${SPECBASE}_$(date +%Y-%m-%d_%H.%M.%S).txt"

IN_TOPICS="$(awk -F'[: ]+' '/^in / {print $2}' $SPECFILE | tr '\n' ' ' | sed 's/ *$//')"
OUT_TOPICS="$(awk -F'[: ]+' '/^out / {print $2}' $SPECFILE | tr '\n' ' ' | sed 's/ *$//')"

CMD="docker run --network host -it --rm -e RUST_BACKTRACE=full -v $HOSTDIR:/mnt/host_models localhost/trustworthiness-checker /mnt/host_models/$SPECBASE --input-mqtt-topics $IN_TOPICS"

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
} | ts -i " (%.S)]" | ts "[%H:%M:%.S" |  tee -a "$LOGFILE" | sed -u -e "s/$/\r/g"
