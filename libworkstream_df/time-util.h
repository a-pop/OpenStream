#ifndef TIME_UTIL_H
#define TIME_UTIL_H

#include <time.h>

static inline int timespec_diff (struct timespec *,
				 const struct timespec *,
				 const struct timespec *);

#define BEGIN_TIME(p) clock_gettime (CLOCK_THREAD_CPUTIME_ID, (p))
#define END_TIME(p)						\
do								\
  {								\
    struct timespec _end_time_tv;				\
    clock_gettime (CLOCK_THREAD_CPUTIME_ID, &_end_time_tv);	\
    assert (timespec_diff ((p), &_end_time_tv, (p)) == 0);	\
  }								\
while (0)

static inline int
timespec_diff (struct timespec *_result,
	       const struct timespec *_px, const struct timespec *_py)
{
  struct timespec _x, _y;

  _x = *_px;
  _y = *_py;

  /* Perform the carry for the later subtraction by updating y. */
  if (_x.tv_nsec < _y.tv_nsec) {
    long _ns = (_y.tv_nsec - _x.tv_nsec) / 1000000000L + 1;
    _y.tv_nsec -= 1000000000L * _ns;
    _y.tv_sec += _ns;
  }
  if (_x.tv_nsec - _y.tv_nsec > 1000000000L) {
    long _ns = (_x.tv_nsec - _y.tv_nsec) / 1000000000L;
    _y.tv_nsec += 1000000000L * _ns;
    _y.tv_sec -= _ns;
  }

  /* Compute the time remaining to wait. tv_nsec is certainly
     positive. */
  _result->tv_sec = _x.tv_sec - _y.tv_sec;
  _result->tv_nsec = _x.tv_nsec - _y.tv_nsec;

  /* Return 1 if result is negative. */
  return _x.tv_sec < _y.tv_sec;
}

#endif