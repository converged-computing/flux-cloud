#!/usr/bin/python

# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import pytest

from fluxcloud.main.settings import UserSettings

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)

from .helpers import get_settings  # noqa


def test_invalid_properties(tmp_path):
    """
    Test invalid setting property
    """
    settings = UserSettings(get_settings(tmp_path))
    assert settings.config_editor == "vim"
    settings.set("config_editor", "code")
    with pytest.raises(SystemExit):
        settings.set("invalid_key", "invalid_value")
    assert settings.config_editor == "code"


def test_set_get(tmp_path):
    """
    Test variable set/get
    """
    settings = UserSettings(get_settings(tmp_path))

    zone = "us-central1-a"
    assert settings.google["zone"] == zone

    # Cannot add invalid parameter
    with pytest.raises(SystemExit):
        settings.set("cache_only", True)

    found_zone = settings.get("google:zone")
    assert isinstance(zone, str)
    assert zone == found_zone

    # Just check the first in the list
    assert settings.google["zone"] == zone
