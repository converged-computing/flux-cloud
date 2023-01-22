# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import time
from functools import partial, update_wrapper


class Decorator:
    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)


class save_meta(Decorator):
    """
    Call to save metadata on the class with setup and experiment
    """

    def __call__(self, cls, *args, **kwargs):

        # Name of the key is after command
        idx = 0
        if "setup" in kwargs:
            setup = kwargs["setup"]
        else:
            setup = args[idx]
            idx += 1

        # experiment is either the second argument or a kwarg
        if "experiment" in kwargs:
            experiment = kwargs["experiment"]
        elif len(args) > 1:
            experiment = args[idx]
        else:
            experiment = None

        res = self.func(cls, *args, **kwargs)
        experiment = experiment or setup.get_single_experiment()
        experiment.save_metadata(cls.times, cls.info)
        cls.clear_minicluster_times()
        return res


class timed(Decorator):
    """
    Time the length of the run, add to times
    """

    def __call__(self, cls, *args, **kwargs):

        # Name of the key is after command
        if "name" in kwargs:
            key = kwargs["name"]
        else:
            key = args[0]

        start = time.time()
        res = self.func(cls, *args, **kwargs)
        end = time.time()
        cls.times[key] = round(end - start, 3)
        return res
