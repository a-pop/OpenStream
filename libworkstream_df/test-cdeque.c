#define _POSIX_C_SOURCE 200112L

#include <assert.h>
#include <math.h>
#include <pthread.h>
#include <sched.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "papi-defs.h"
#include "wstream_df.h"
#include "error.h"
#include "cdeque.h"
#include "time-util.h"

struct state
{
  unsigned long id __attribute__ ((aligned (64)));
  pthread_t tid;
  struct timespec time;
  unsigned long num_attempt;
  unsigned long num_failed_attempt;
  unsigned int seed;
};

struct state *states;
static cdeque_t *worker_deque;

static unsigned long num_thread, num_job, num_steal, num_steal_per_thread;
static double steal_freq;
static unsigned long breadth, depth;

static volatile unsigned long num_start_spin = 1000000000UL;
static atomic_bool start __attribute__ ((aligned (64)));
static atomic_bool end __attribute__ ((aligned (64)));

static void *worker_main (void *);
static void worker (struct state *, unsigned long);
static void straight_worker (struct state *, unsigned long);
static void *thief_main (void *);

static void *
worker_main (void *data)
{
  struct state *state = data;
  unsigned long i;

  for (i = 0; i < num_start_spin; ++i)
    continue;

  if (breadth == 1)
    straight_worker (state, depth);
  else
    {
      BEGIN_TIME (&state->time);
      atomic_store_explicit (&start, true, memory_order_release);
      worker (state, depth);
    }
  END_TIME (&state->time);
  atomic_store_explicit (&end, true, memory_order_release);

  return NULL;
}

static void
worker (struct state *state, unsigned long d)
{
  void *val;
  double dummy;
  unsigned long b;

  if (d == 0)
    return;
  for (b = 0; b < breadth; ++b)
    {
      dummy = (double) rand_r (&state->seed) / RAND_MAX;
      cdeque_push_bottom (worker_deque, &dummy);
      worker (state, d - 1);
      val = cdeque_take (worker_deque);
      if (val == NULL)
	++state->num_failed_attempt;
      else
	assert (*(double *) val == dummy);
      ++state->num_attempt;
    }
}

static void
straight_worker (struct state *state, unsigned long d)
{
  void *val;
  unsigned long i;

  for (i = 0; i < d; ++i)
    cdeque_push_bottom (worker_deque, (void *) i);

  BEGIN_TIME (&state->time);
  atomic_store_explicit (&start, true, memory_order_release);

  while (i-- > 0)
    {
      val = cdeque_take (worker_deque);
      if (val == NULL)
	++state->num_failed_attempt;
      else
	assert ((unsigned long) val == i);
      ++state->num_attempt;
    }
}

static void *
thief_main (void *data)
{
  struct state *state = data;
  void *val;
  double stealprob;
  unsigned long i;

  while (!atomic_load_explicit (&start, memory_order_acquire))
    continue;

  BEGIN_TIME (&state->time);

  if (steal_freq > 0.0)
    stealprob = steal_freq;
  else
    stealprob = (double) num_steal_per_thread / num_job;
  for (i = 0; i < num_steal_per_thread; ++i)
    {
      /* Minimal probability is actually 1/RAND_MAX. */
      while ((double) rand_r (&state->seed) / RAND_MAX > stealprob)
	continue;
      val = cdeque_steal (worker_deque);
      if (val == NULL)
	++state->num_failed_attempt;
      if (!atomic_load_explicit (&end, memory_order_acquire))
	++state->num_attempt;
    }

  END_TIME (&state->time);

  return NULL;
}

int
main (int argc, char *argv[])
{
  pthread_attr_t thrattr;
  cpu_set_t cpuset;
  double stealratio;
  size_t dqlogsize;
  unsigned long d, t, n, nrowjob;
  int opt;

  num_thread = 2;
  num_steal = -1;
  stealratio = 0.01;
  breadth = 6;
  depth = 10;
  dqlogsize = 6;
  while ((opt = getopt (argc, argv, "b:d:f:i:n:p:r:s:")) != -1)
    {
      switch (opt)
	{
	case 'b':
	  breadth = strtoul (optarg, NULL, 0);
	  if (breadth < 1)
	    {
	      fprintf (stderr, "-b BREADTH must be greater or equal to 1\n");
	      return EXIT_FAILURE;
	    }
	  break;

	case 'd':
	  depth = strtoul (optarg, NULL, 0);
	  if (depth < 1)
	    {
	      fprintf (stderr, "-d DEPTH must be greater or equal to 1\n");
	      return EXIT_FAILURE;
	    }
	  break;

	case 'f':
	  steal_freq = strtod (optarg, NULL);
	  if (steal_freq < 0.0)
	    {
	      fprintf (stderr,
		       "-f STEAL_FREQ must be greater or equal to 0.0\n");
	      return EXIT_FAILURE;
	    }
	  break;

	case 'i':
	  dqlogsize = strtoul (optarg, NULL, 0);
	  break;

	case 'n':
	  num_thread = strtoul (optarg, NULL, 0);
	  if (num_thread < 2)
	    {
	      fprintf (stderr, "-n NUM_THREAD must be greater or equal to 2\n");
	      return EXIT_FAILURE;
	    }
	  break;

	case 'r':
	  srand (strtoul (optarg, NULL, 0));
	  break;

	case 's':
	  if (strchr (optarg, '.') == NULL)
	    {
	      num_steal = strtoul (optarg, NULL, 0);
	      stealratio = -1.0;
	    }
	  else
	    {
	      num_steal = -1;
	      stealratio = strtod (optarg, NULL);
	    }
	  break;

	default:
	  fprintf (stderr,
		   "Usage: %s [OPTIONS]\n"
		   "Options:\n"
		   "  -b BREADTH\n"
		   "  -d DEPTH\n"
		   "  -f STEAL_FREQ\n"
		   "  -i INI_DEQUE_LOG_SIZE\n"
		   "  -n NUM_THREAD\n"
		   "  -r RAND_SEED\n"
		   "  -s NUM_STEAL_OR_RATIO\n",
		   argv[0]);
	  return EXIT_FAILURE;
	}
    }

  nrowjob = breadth;
  for (d = 0; d < depth; ++d)
    {
      nrowjob *= breadth;
      num_job += nrowjob;
    }

  if (stealratio >= 0.0)
    num_steal = (unsigned long) (stealratio * num_job);
  num_steal_per_thread = num_steal / (num_thread - 1);
  num_steal = num_steal_per_thread * (num_thread - 1);

  worker_deque = cdeque_alloc (dqlogsize);
  assert (worker_deque != NULL);

  states = calloc (num_thread, sizeof *states);
  assert (states != NULL);

  states[0].seed = rand ();
  for (t = 1; t < num_thread; ++t)
    {
      states[t].id = t;
      states[t].seed = rand ();

      pthread_attr_init (&thrattr);
      CPU_ZERO (&cpuset);
      CPU_SET (t, &cpuset);
#if !NO_TEST_SETAFFINITY
      assert (pthread_attr_setaffinity_np (&thrattr,
					   sizeof cpuset, &cpuset) == 0);
#endif
      assert (pthread_create (&states[t].tid, &thrattr,
			      thief_main, &states[t]) == 0);
    }

  pthread_attr_init (&thrattr);
  CPU_ZERO (&cpuset);
  CPU_SET (0, &cpuset);
#if !NO_TEST_SETAFFINITY
  assert (pthread_attr_setaffinity_np (&thrattr, sizeof cpuset, &cpuset) == 0);
#endif
  assert (pthread_create (&states[0].tid, &thrattr,
			  worker_main, &states[0]) == 0);

  assert (pthread_join (states[0].tid, NULL) == 0);
  for (t = 1; t < num_thread; ++t)
    assert (pthread_join (states[t].tid, NULL) == 0);

  printf ("worker_time\t");
  for (t = 1; t < num_thread; ++t)
    printf ("thief_time_%lu\t", t);
  printf ("take_empty_count\t"
	  "steal_empty_count\t"
	  "num_job\t"
	  "num_expected_steal\t"
	  "num_effective_steal\n");

  printf ("%ld.%09ld\t", states[0].time.tv_sec, states[0].time.tv_nsec);
  for (t = 1; t < num_thread; ++t)
    printf ("%ld.%09ld\t", states[t].time.tv_sec, states[t].time.tv_nsec);

  printf ("%lu\t", states[0].num_failed_attempt);
  n = 0;
  for (t = 1; t < num_thread; ++t)
    n += states[t].num_failed_attempt;
  printf ("%lu\t", n);

  printf ("%lu\t", num_job);
  printf ("%lu\t", num_steal);
  n = 0;
  for (t = 1; t < num_thread; ++t)
    n += states[t].num_attempt;
  printf ("%lu\n", n);

  free (states);

  cdeque_free (worker_deque);

  return 0;
}
