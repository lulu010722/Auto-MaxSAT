#!/bin/bash
#$1: instance file
#$2: seed
#$3: cutoff time
wl=$3

./auto_src/runsolver --timestamp -d 15 -o output.out -v output.var -w output.wat -C $wl -W $wl ./solver_src/bin/USW-LS $1 $2
cat output.out
rm -f output.out
rm -f output.var
rm -f output.wat
