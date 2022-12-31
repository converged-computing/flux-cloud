# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import time
from functools import partial, update_wrapper


class timed:
    """
    Time the length of the run, add to times
    """

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)

    def __call__(self, cls, *args, **kwargs):

        # Name of the key is after command
        if "name" in kwargs:
            key = kwargs["name"]
        else:
            key = args[0]

        start = time.time()
        res = self.func(cls, *args, **kwargs)
        end = time.time()
        cls.times[key] = end - start
        return res


class job_timed(timed):
    """
    time the job and add to a custom lookup of times (not cluster)
    """

    def __call__(self, cls, *args, **kwargs):

        # Name of the key is after command
        if "name" in kwargs:
            key = kwargs["name"]
        else:
            key = args[0]

        if "times" in kwargs:
            times = kwargs["times"]
        else:
            times = args[-1]

        start = time.time()
        res = self.func(cls, *args, **kwargs)
        end = time.time()
        times[key] = end - start
        return res
