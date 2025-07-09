#!/bin/bash
#$1: instance file
#$2: seed
#$3: cutoff time
wl=$3

pid=$$

./auto_src/runsolver --timestamp -d 15 -o output_$pid.out -v output_$pid.var -w output_$pid.wat -C $wl -W $wl ./solver_src/bin/USW-LS $1 $2
cat output_$pid.out
rm -f output_$pid.out
rm -f output_$pid.var
rm -f output_$pid.wat
