#ifndef __SLAB_ALLOCATOR_H_
#define __SLAB_ALLOCATOR_H_

#include <assert.h>
#include <stdlib.h>

#define __slab_align 64
#define __slab_min_size 6 // 64 -- smallest slab
#define __slab_max_size 20 // 262144 = 256KB -- biggest slab
#define __slab_alloc_size 21 // 1048576 = 1MB -- amount of memory that should be allocated in one go

#if !NO_SLAB_ALLOCATOR
  #define WSTREAM_DF_THREAD_SLAB_FIELDS \
   slab_cache_t slab_cache
#else
  #define WSTREAM_DF_THREAD_SLAB_FIELDS
#endif

typedef struct slab
{
  struct slab * next;

} slab_t, *slab_p;

typedef struct slab_metainfo {
	int allocator_id;
	unsigned int size;
} slab_metainfo_t, *slab_metainfo_p;

#define ROUND_UP(x,y) (((x)+(y)-1)/(y))
#define __slab_metainfo_size (ROUND_UP(sizeof(slab_metainfo_t), __slab_align)*__slab_align)

typedef struct slab_cache {
  slab_p slab_free_pool[__slab_max_size + 1];

  unsigned long long slab_bytes;
  unsigned long long slab_refills;
  unsigned long long slab_allocations;
  unsigned long long slab_frees;
  unsigned long long slab_freed_bytes;
  unsigned long long slab_hits;
  unsigned long long slab_toobig;
  unsigned long long slab_toobig_frees;
  unsigned long long slab_toobig_freed_bytes;
  unsigned int allocator_id;
} slab_cache_t, *slab_cache_p;

static inline unsigned int
get_slab_index (unsigned int size)
{
  unsigned int leading_nonzero_pos = 32 - __builtin_clz (size) - 1;
  unsigned int size_2 = 1 << leading_nonzero_pos;
  unsigned int idx = leading_nonzero_pos;

  if ((size ^ size_2) != 0)
    idx = idx + 1;
  if (idx < __slab_min_size)
    idx = __slab_min_size;

  return idx;
}

static inline slab_metainfo_p
slab_metainfo(void* ptr)
{
  return (slab_metainfo_p)(((char*)ptr) - __slab_metainfo_size);
}

static inline unsigned int
slab_allocator_of(void* ptr)
{
  slab_metainfo_p metainfo = slab_metainfo(ptr);
  return metainfo->allocator_id;
}

static inline void
slab_refill (slab_cache_p slab_cache, unsigned int idx)
{
  const unsigned int num_slabs = 1 << (__slab_alloc_size - idx);
  const unsigned int slab_size = 1 << idx;
  unsigned int i;
  slab_p s;
  void* alloc = NULL;
  slab_metainfo_p metainfo;

  assert (!posix_memalign (&alloc,
			   __slab_align,
			   (1 << __slab_alloc_size) +
			   __slab_metainfo_size * num_slabs));

  slab_cache->slab_free_pool[idx] = (slab_p)(((char*)alloc) + __slab_metainfo_size);
  slab_cache->slab_refills++;
  slab_cache->slab_bytes += 1 << __slab_alloc_size;

  s = slab_cache->slab_free_pool[idx]; // avoid useless warning;
  for (i = 0; i < num_slabs - 1; ++i)
    {
      metainfo = slab_metainfo(s);
      metainfo->allocator_id = slab_cache->allocator_id;
      s->next = (slab_p) (((char *) s) + slab_size + __slab_metainfo_size);
      s = s->next;
    }
  s->next = NULL;
}

static inline void *
slab_alloc (slab_cache_p slab_cache, unsigned int size)
{
  unsigned int idx = get_slab_index (size);
  void *res;
  slab_metainfo_p metainfo;

  slab_cache->slab_allocations++;

  if (idx > __slab_max_size)
    {
      slab_cache->slab_toobig++;
      assert (!posix_memalign ((void **) &res, __slab_align, size + __slab_metainfo_size));
      metainfo = res;
      metainfo->size = size;
      metainfo->allocator_id = slab_cache->allocator_id;
      return (((char*)res) + __slab_metainfo_size);
    }

  if (slab_cache->slab_free_pool[idx] == NULL)
    slab_refill (slab_cache, idx);
  else
    slab_cache->slab_hits++;

  res = (void *) slab_cache->slab_free_pool[idx];
  slab_cache->slab_free_pool[idx] = slab_cache->slab_free_pool[idx]->next;

  metainfo = slab_metainfo(res);
  metainfo->size = size;

  return res;
}

static inline void
slab_free (slab_cache_p slab_cache, void *e)
{
  slab_p elem = (slab_p) e;
  slab_metainfo_p metainfo = slab_metainfo(e);
  unsigned int idx = get_slab_index (metainfo->size);

  if (idx > __slab_max_size)
    {
      slab_cache->slab_toobig_frees++;
      slab_cache->slab_toobig_freed_bytes += metainfo->size;
      free (slab_metainfo(e));
    }
  else
    {
      elem->next = slab_cache->slab_free_pool[idx];
      slab_cache->slab_free_pool[idx] = elem;
      slab_cache->slab_frees++;
      slab_cache->slab_freed_bytes += metainfo->size;
    }
}

static inline void
slab_init_allocator (slab_cache_p slab_cache, unsigned int allocator_id)
{
  int i;

  for (i = 0; i < __slab_max_size + 1; ++i)
    slab_cache->slab_free_pool[i] = NULL;

  slab_cache->allocator_id = allocator_id;
  slab_cache->slab_bytes = 0;
  slab_cache->slab_refills = 0;
  slab_cache->slab_allocations = 0;
  slab_cache->slab_frees = 0;
  slab_cache->slab_freed_bytes = 0;
  slab_cache->slab_hits = 0;
  slab_cache->slab_toobig = 0;
  slab_cache->slab_toobig_frees = 0;
  slab_cache->slab_toobig_freed_bytes = 0;
}


#undef __slab_align
#undef __slab_min_size
#undef __slab_max_size
#undef __slab_alloc_size

#if !NO_SLAB_ALLOCATOR
#  define wstream_alloc(SLAB, PP,A,S)			\
  *(PP) = slab_alloc ((SLAB), (S))
#  define wstream_free(SLAB, P)			\
  slab_free ((SLAB), (P))
#  define wstream_init_alloc(SLAB, ID)		\
  slab_init_allocator (SLAB, ID)
#  define wstream_allocator_of(P)		\
  slab_allocator_of(P)
#else
#  define wstream_alloc(SLAB, PP,A,S)			\
  assert (!posix_memalign ((void **) (PP), (A), (S)))
#  define wstream_free(SLAB, P)			\
  free ((P))
#  define wstream_init_alloc(SLAB, ID)
#  define wstream_allocator_of(P) (-1)
#endif


#endif
