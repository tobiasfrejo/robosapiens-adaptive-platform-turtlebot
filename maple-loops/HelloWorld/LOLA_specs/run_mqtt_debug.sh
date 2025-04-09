#!/bin/bash

SPECFILE="$(realpath "$1")"
SPECBASE="$(basename "$SPECFILE")"
HOSTDIR="$(dirname "$SPECFILE")"

IN_TOPICS="$(awk -F'[: ]+' '/^in / {print $2}' $SPECFILE | tr '\n' ' ' | sed 's/ *$//')"
OUT_TOPICS="$(awk -F'[: ]+' '/^out / {print $2}' $SPECFILE | tr '\n' ' ' | sed 's/ *$//')"

CMD="docker run --network host -it --rm -e RUST_BACKTRACE=full -v $HOSTDIR:/mnt/host_models trustworthiness-checker:debug /mnt/host_models/$SPECBASE --input-mqtt-topics $IN_TOPICS  --output-mqtt-topics $OUT_TOPICS --output-mqtt-topic-prefix lola/$SPECBASE/"

{
echo "Command: $CMD"
echo ""
echo "========     SPECIFICATION      ======="
echo "Source: $SPECBASE"
cat "$SPECFILE"
echo ""
echo ""
echo "======== TRUSTWORTHINESS OUTPUT ======="
$CMD
}
