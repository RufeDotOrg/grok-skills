// main first, definitions last: implicit declaration all the way
main()
{
  greet("slicefn");
  printf("fib(20) = %d\n", fib(20));
  printf("gcd(84, 36) = %d\n", gcd(84, 36));
  return 0;
}

#include "demo.slicefn.c"
