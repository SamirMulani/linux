"""
mem-phys-addr.py: Resolve physical address samples
"""
# SPDX-License-Identifier: GPL-2.0
#
# Copyright (c) 2018, Intel Corporation.

from __future__ import division
from __future__ import print_function

import os
import sys
import re
import bisect
import collections

sys.path.append(os.environ['PERF_EXEC_PATH'] + \
	'/scripts/python/Perf-Trace-Util/lib/Perf/Trace')

#physical address ranges for System RAM
system_ram = []
#physical address ranges for Persistent Memory
pmem = []
#file object for proc iomem
F = None
#Count for each type of memory
load_mem_type_cnt = collections.Counter()
#perf event name
EVENT_NAME = None

def parse_iomem():
    """
    Parse the /proc/iomem file to extract information about System RAM and Persistent Memory.
    """
    global F
    with open('/proc/iomem', 'r', encoding='utf-8') as F:
        for j in enumerate(F):
            mem = re.split('-|:',j,2)
            if mem[2].strip() == 'System RAM':
                system_ram.append(int(mem[0], 16))
                system_ram.append(int(mem[1], 16))
            if mem[2].strip() == 'Persistent Memory':
                pmem.append(int(mem[0], 16))
                pmem.append(int(mem[1], 16))

def print_memory_type():
    """
    Print summary of memory types, counts, and percentages.
    """
    print(f"Event: {EVENT_NAME}")
    print(f"{'Memory type':<40}  {'count':>10}  {'percentage':>10}\n", end='')
    print(f"{'-' * 40:<40}  {'-' * 10:>10}  {'-' * 10:>10}\n", end='')
    total = sum(load_mem_type_cnt.values())
    for mem_type, count in sorted(load_mem_type_cnt.most_common(), \
					key = lambda kv: (kv[1], kv[0]), reverse = True):
        print(f"{mem_type:<40}  {count:>10}  {100 * count / total:>10.1f}%")

def trace_begin():
    """
    Begin tracing process by parsing /proc/iomem.
    """
    parse_iomem()

def trace_end():
    """
    End tracing process and print memory type summary.
    """
    print_memory_type()
    F.close()

def is_system_ram(phys_addr):
    """
    Check if a physical address belongs to System RAM.
    """
    #/proc/iomem is sorted
    position = bisect.bisect(system_ram, phys_addr)
    if position % 2 == 0:
        return False
    return True

def is_persistent_mem(phys_addr):
    """
    Check if a physical address belongs to Persistent Memory.
    """
    position = bisect.bisect(pmem, phys_addr)
    if position % 2 == 0:
        return False
    return True

def find_memory_type(phys_addr):
    """
    Find the memory type of a physical address.
    """
    if phys_addr == 0:
        return "N/A"
    if is_system_ram(phys_addr):
        return "System RAM"

    if is_persistent_mem(phys_addr):
        return "Persistent Memory"

    #slow path, search all
    F.seek(0, 0)
    for j in F:
        mem = re.split('-|:',j,2)
        if int(mem[0], 16) <= phys_addr <= int(mem[1], 16):
            return mem[2]
    return "N/A"

def process_event(param_dict):
    """
    Process an event and update memory type count.
    """
    name       = param_dict["ev_name"]
    sample     = param_dict["sample"]
    phys_addr  = sample["phys_addr"]

    global EVENT_NAME
    if EVENT_NAME is None:
        EVENT_NAME = name
    load_mem_type_cnt[find_memory_type(phys_addr)] += 1
