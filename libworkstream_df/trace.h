#ifndef TRACE_H
#define TRACE_H

#include <stdint.h>

#include "config.h"

#define WQEVENT_STATECHANGE 0
#define WQEVENT_SINGLEEVENT 1
#define WQEVENT_STEAL 2
#define WQEVENT_TCREATE 3
#define WQEVENT_PUSH 4
#define WQEVENT_START_TASKEXEC 5
#define WQEVENT_END_TASKEXEC 6

#define WORKER_STATE_SEEKING 0
#define WORKER_STATE_TASKEXEC 1
#define WORKER_STATE_RT_TCREATE 2
#define WORKER_STATE_RT_RESDEP 3
#define WORKER_STATE_RT_TDEC 4
#define WORKER_STATE_RT_BCAST 5
#define WORKER_STATE_MAX 6

#define TASK_DURATION_PUSH_SAMEL1 0
#define TASK_DURATION_PUSH_SAMEL2 1
#define TASK_DURATION_PUSH_SAMEL3 2
#define TASK_DURATION_PUSH_REMOTE 3
#define TASK_DURATION_STEAL_SAMEL2 4
#define TASK_DURATION_STEAL_SAMEL3 5
#define TASK_DURATION_STEAL_REMOTE 6
#define TASK_DURATION_MAX 7

typedef struct worker_event {
  uint64_t time;
  uint32_t type;

  union {
    struct {
      uint32_t src;
      uint32_t size;
    } steal;

    struct {
      uint32_t from_node;
      uint32_t type;
    } texec;

    struct {
      uint32_t dst;
      uint32_t size;
    } push;

    struct {
      uint32_t state;
      uint32_t previous_state_idx;
    } state_change;
  };
} worker_state_change_t, *worker_state_change_p;

#if ALLOW_WQEVENT_SAMPLING
struct wstream_df_thread;

void trace_event(struct wstream_df_thread* cthread, unsigned int type);
void trace_task_exec_start(struct wstream_df_thread* cthread, unsigned int from_node, unsigned int type);
void trace_task_exec_end(struct wstream_df_thread* cthread);
void trace_state_change(struct wstream_df_thread* cthread, unsigned int state);
void trace_state_restore(struct wstream_df_thread* cthread);
void trace_steal(struct wstream_df_thread* cthread, unsigned int src, unsigned int size);
void trace_push(struct wstream_df_thread* cthread, unsigned int dst, unsigned int size);

void dump_events(int num_workers, struct wstream_df_thread* wstream_df_worker_threads);
void dump_average_task_durations(int num_workers, struct wstream_df_thread* wstream_df_worker_threads);
void dump_avg_state_parallelism(unsigned int state, uint64_t max_intervals, int num_workers, struct wstream_df_thread* wstream_df_worker_threads);

#else
#define trace_task_exec_end(cthread) do { } while(0)
#define trace_task_exec_start(cthread, from_node, type) do { } while(0)
#define trace_event(cthread, type) do { } while(0)
#define trace_state_change(cthread, state) do { } while(0)
#define trace_steal(cthread, src, size) do { } while(0)
#define trace_push(cthread, src, size) do { } while(0)
#define trace_state_restore(cthread) do { } while(0)

#define dump_events(num_workers, wstream_df_worker_threads)  do { } while(0)
#define dump_average_task_durations(num_workers, wstream_df_worker_threads) do { } while(0)
#define dump_avg_state_parallelism(state, max_intervals, num_workers, wstream_df_worker_threads) do { } while(0)
#endif

#endif