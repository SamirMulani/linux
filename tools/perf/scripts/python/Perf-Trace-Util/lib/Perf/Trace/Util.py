"""
Util.py - Python extension for perf script, miscellaneous utility code

Copyright (C) 2010 by Tom Zanussi <tzanussi@gmail.com>

This software may be distributed under the terms of the GNU General
Public License ("GPL") version 2 as published by the Free Software
Foundation.
"""
from __future__ import print_function

import errno
import os

FUTEX_WAIT = 0
FUTEX_WAKE = 1
FUTEX_PRIVATE_FLAG = 128
FUTEX_CLOCK_REALTIME = 256
FUTEX_CMD_MASK = ~(FUTEX_PRIVATE_FLAG | FUTEX_CLOCK_REALTIME)

NSECS_PER_SEC = 1000000000


def avg(total, num_elements):
    """Calculate the average of a total sum."""
    return total / num_elements


def nsecs(secs, nanosecs):
    """Convert seconds and nanoseconds to total nanoseconds."""
    return secs * NSECS_PER_SEC + nanosecs


def nsecs_secs(nanosecs):
    """Extract seconds from total nanoseconds."""
    return nanosecs // NSECS_PER_SEC


def nsecs_nsecs(nanosecs):
    """Extract nanoseconds from total nanoseconds."""
    return nanosecs % NSECS_PER_SEC


def nsecs_str(nanosecs):
    """Convert total nanoseconds to a formatted string."""
    return "{:5d}.{:09d}".format(nsecs_secs(nanosecs), nsecs_nsecs(nanosecs))


def add_stats(stats_dict, key, value):
    """Add statistics to a dictionary."""
    if key not in stats_dict:
        stats_dict[key] = (value, value, value, 1)
    else:
        min_value, max_value, avg_value, count = stats_dict[key]
        if value < min_value:
            min_value = value
        if value > max_value:
            max_value = value
        avg_value = (avg_value + value) / 2
        stats_dict[key] = (min_value, max_value, avg_value, count + 1)


def clear_term():
    """Clear the terminal screen."""
    print("\x1b[H\x1b[2J")


AUDIT_PACKAGE_WARNED = False

try:
    import audit
    MACHINE_TO_ID = {
        'x86_64': audit.MACH_86_64,
        'alpha': audit.MACH_ALPHA,
        'ia64': audit.MACH_IA64,
        'ppc': audit.MACH_PPC,
        'ppc64': audit.MACH_PPC64,
        'ppc64le': audit.MACH_PPC64LE,
        's390': audit.MACH_S390,
        's390x': audit.MACH_S390X,
        'i386': audit.MACH_X86,
        'i586': audit.MACH_X86,
        'i686': audit.MACH_X86,
    }
    try:
        MACHINE_TO_ID['armeb'] = audit.MACH_ARMEB
    except AttributeError:
        pass
    MACHINE_ID = MACHINE_TO_ID[os.uname()[4]]
except ImportError:
    if not AUDIT_PACKAGE_WARNED:
        AUDIT_PACKAGE_WARNED = True
        print("Install the audit-libs-python package to get syscall names.\n"
              "For example:\n  # apt-get install python-audit (Ubuntu)"
              "\n  # yum install audit-libs-python (Fedora)"
              "\n  etc.\n")


def syscall_name(syscall_id):
    """Get the name of a syscall using its ID."""
    try:
        return audit.audit_syscall_to_name(syscall_id, MACHINE_ID)
    except AttributeError:
        return str(syscall_id)


def strerror(errno_value):
    """Convert an errno value to a human-readable string."""
    try:
        return errno.errorcode[abs(errno_value)]
    except KeyError:
        return "Unknown {} errno".format(errno_value)
