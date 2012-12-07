#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <complex.h>

#include <getopt.h>

#define _WITH_OUTPUT 0

#include <sys/time.h>
#include <unistd.h>
#include "../common/sync.h"

double
tdiff (struct timeval *end, struct timeval *start)
{
  return (double)end->tv_sec - (double)start->tv_sec +
    (double)(end->tv_usec - start->tv_usec) / 1e6;
}


int
fibo (int n)
{
  if (n < 2)
    return n;

  return fibo (n-1) + fibo (n-2);
}

int
main (int argc, char **argv)
{
  int option;
  int i, j, iter;
  int n = 15;

  int result;

  struct timeval *start = (struct timeval *) malloc (sizeof (struct timeval));
  struct timeval *end = (struct timeval *) malloc (sizeof (struct timeval));

  struct profiler_sync sync;

  PROFILER_NOTIFY_PREPARE(&sync);

  while ((option = getopt(argc, argv, "n:h")) != -1)
    {
      switch(option)
	{
	case 'n':
	  n = atoi(optarg);
	  break;
	case 'h':
	  printf("Usage: %s [option]...\n\n"
		 "Options:\n"
		 "  -n <number>                  Calculate fibonacci number <number>, default is %d\n",
		 argv[0], n);
	  exit(0);
	  break;
	case '?':
	  fprintf(stderr, "Run %s -h for usage.\n", argv[0]);
	  exit(1);
	  break;
	}
    }

  if(optind != argc) {
	  fprintf(stderr, "Too many arguments. Run %s -h for usage.\n", argv[0]);
	  exit(1);
  }

  gettimeofday (start, NULL);
  PROFILER_NOTIFY_RECORD(&sync);
  result = fibo (n);
  PROFILER_NOTIFY_PAUSE(&sync);
  gettimeofday (end, NULL);

  printf ("%.5f\n", tdiff (end, start));

  if (_WITH_OUTPUT)
    printf ("Fibo (%d) = %d\n", n, result);

  PROFILER_NOTIFY_FINISH(&sync);
}
