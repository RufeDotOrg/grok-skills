#!/bin/sh
# walk through slicefn.py with C: demo.slicefn + demo.sliceindex, compiled via #include
set -e
cd "$(dirname "$0")"
PATH="$PWD/../../../slicefn:$PATH"
CC=${CC:-clang}
CFLAGS="-O1 -g1 -ferror-limit=3 -Wno-implicit-function-declaration -Wno-implicit-int -Wno-return-type -Wno-deprecated-non-prototype -Wno-incompatible-function-pointer-types"
rm -f demo.slicefn demo.sliceindex demo

echo "== put greet"
printf 'greet(char *who)\n{\n  printf("hello, %%s\\n", who);\n}\n' | slicefn.py --ruffc demo.slicefn put greet

echo "== put fib (grows the pair)"
printf 'fib(int n)\n{\n  int a = 0, b = 1, t;\n  while (n--) t = a + b, a = b, b = t;\n  return a;\n}\n' | slicefn.py --ruffc demo.slicefn put fib

echo "== put gcd"
printf 'gcd(int a, int b)\n{\n  return b ? gcd(b, a %% b) : a;\n}\n' | slicefn.py --ruffc demo.slicefn put gcd

echo "== --ruffc rejects a float by value"
printf 'half(float x)\n{\n  return x / 2;\n}\n' | slicefn.py --ruffc demo.slicefn put half || echo "(rejected, rc=$?)"

echo "== index"
cat -n demo.sliceindex

echo "== grep -bo 'return' | at"
grep -bo 'return' demo.slicefn | slicefn.py demo.slicefn at

echo "== build and run"
$CC main.c $CFLAGS -o demo
./demo
