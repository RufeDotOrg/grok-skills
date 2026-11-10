#!/bin/sh
# walk through slicefn.py on a fresh pair: demo.slicefn + demo.sliceindex
set -e
cd "$(dirname "$0")"
PATH="$PWD/../../../slicefn:$PATH"
rm -f demo.slicefn demo.sliceindex

echo "== put greet"
printf 'def greet(who):\n    return "hello, " + who\n' | slicefn.py demo.slicefn put greet

echo "== put fib (grows the pair)"
printf 'def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n' | slicefn.py demo.slicefn put fib

echo "== index"
cat -n demo.sliceindex

echo "== get fib"
slicefn.py demo.slicefn get fib

echo "== grep -bo 'return' | at"
grep -bo 'return' demo.slicefn | slicefn.py demo.slicefn at

echo "== run main.py"
python3 main.py

echo "== put greet again (bigger, moves)"
python3 -c "print('def greet(who):\n    # ' + 'x' * 1100 + '\n    return \"hi, \" + who')" | slicefn.py demo.slicefn put greet
cat demo.sliceindex

echo "== clear fib"
slicefn.py demo.slicefn clear fib
cat -n demo.sliceindex
