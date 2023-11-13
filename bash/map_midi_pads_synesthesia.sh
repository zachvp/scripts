#! /bin/bash

# TODO: add health check support
echo "starting script"

RED=15
GREEN=60
ORANGE=63

# leftmost quadrant - meta toggles, triggers
sendmidi dev "Launch Control XL" ch 1 on 41 $RED
sendmidi dev "Launch Control XL" ch 1 on 42 $RED
sendmidi dev "Launch Control XL" ch 1 on 73 $GREEN
sendmidi dev "Launch Control XL" ch 1 on 74 $RED

# middle section - scene toggles
sendmidi dev "Launch Control XL" ch 1 on 43 $ORANGE
sendmidi dev "Launch Control XL" ch 1 on 44 $ORANGE
sendmidi dev "Launch Control XL" ch 1 on 57 $ORANGE
sendmidi dev "Launch Control XL" ch 1 on 58 $ORANGE

sendmidi dev "Launch Control XL" ch 1 on 75 $ORANGE
sendmidi dev "Launch Control XL" ch 1 on 76 $ORANGE
sendmidi dev "Launch Control XL" ch 1 on 89 $ORANGE
sendmidi dev "Launch Control XL" ch 1 on 90 $ORANGE

# rightmost quadrant - scene triggers
sendmidi dev "Launch Control XL" ch 1 on 59 $GREEN
sendmidi dev "Launch Control XL" ch 1 on 60 $GREEN
sendmidi dev "Launch Control XL" ch 1 on 91 $GREEN
sendmidi dev "Launch Control XL" ch 1 on 92 $GREEN

# scene playlist actions
sendmidi dev "Launch Control XL" ch 1 on 108 $ORANGE

echo "done mapping"
