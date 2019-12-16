#ifndef _FOS_MANAGER_H_
#define _FOS_MANAGER_H_

#include "cynq/cynq.h"
#include "udmalib/udma.h"

#include "wstream_df.h"

class wstream_fpga_env
{
#if !OPENSTREAM_FPGA_DISABLED
public:
  static constexpr unsigned NUMBER_ACCELERATORS = 3;

  UdmaDevice* devices[NUMBER_ACCELERATORS];
  PRManager prmanager;
#endif
};

class wstream_physical_buffer_view
{
public:
  char* ptr;
  long addr;
  int size;
};

extern "C" {

typedef struct wstream_fpga_env  wstream_fpga_env_t;
typedef struct wstream_fpga_env* wstream_fpga_env_p;

wstream_fpga_env_p create_fpga_environment();
void execute_task_on_accelerator(wstream_df_frame_p fp, wstream_fpga_env_p fpga_env_p, int slot_id);
void destroy_fpga_environment(wstream_fpga_env_p fpga_env_p);

}

#endif
