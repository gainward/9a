#!/usr/bin/python2.5
#
# Copyright 2010
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configuration constants."""

DEBUG = True

SERVER_BASE_PATH = '/s'


import sys
_module = sys.modules[__name__]
def get(key, default=None):
  return getattr(_module, key) if hasattr(_module, key) else default
