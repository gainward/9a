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

"""9a backend request handlers."""

__author__ = 'wes.goodman@gmail.com (Wes Goodman)'

import datetime
import logging
import os
import os.path
import re
import sys
import urllib
import wsgiref.handlers

from django.utils import simplejson

from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import config
import jsonrpc
from models import User, Gym, GymMembership
import service_util


template.register_template_library(
    'django.contrib.humanize.templatetags.humanize')
template.register_template_library('templatelib')


@jsonrpc.method('server.info')
def server_info(handler, **kwargs):
  return dict(protocol_version='0.1',
              server='batsignal/0.1')


@jsonrpc.method('users.edit')
@jsonrpc.require_login
def edit_user(handler, user):
  db_user = service_util.get_or_create_user(users.get_current_user())

  warnings = []
  dirty = False
  for k in user:
    if not k in User.EDITABLE_FIELDS:
      warnings.append('Field "%s" is not editable.' % k)
    else:
      dirty = True
      setattr(db_user, k, user[k])

  if dirty:
    db_user.put()

  return dict(warnings=warnings) if warnings else None


@jsonrpc.method('users.get')
# TODO: should this require login?
def get_user(handler, user_id):
  current_user = users.get_current_user()
  if user_id == 'me' or user_id == current_user.user_id():
    db_user = service_util.get_or_create_user(current_user)
  else:
    db_user = User.get_by_key_name(user_id)

  if not db_user:
    raise jsonrpc.JsonRpcError('notfound.user',
                               'User not found.')
  return db_user


@jsonrpc.method('users.search')
# TODO: should this require login?
def search_user(handler, **kwargs):
  if kwargs.has_key('email'):
    user = User.all().filter('email =', kwargs['email'].strip()).get()
  else:
    raise jsonrpc.JsonRpcError('parameters',
                               'You must specify at least one search '
                               'parameter.')

  return dict(user=user)


@jsonrpc.method('gyms.create')
@jsonrpc.require_login
def create_gym(handler, name):
  user = service_util.get_or_create_user(users.get_current_user())
  gym = Gym(name=name)
  gym.put()

  membership = GymMembership(parent=gym,
                             gym=gym,
                             user=user,
                             owner=True)
  membership.put()
  return dict(group=group)


@jsonrpc.method('gyms.list')
@jsonrpc.require_login
def list_groups(handler):
  user = service_util.get_or_create_user(users.get_current_user())

  groups = [m.group for m in user.memberships]
  return dict(groups=groups)


@jsonrpc.method('routes.list')
@jsonrpc.require_login
def list_messages(handler, **kwargs):
  #TODO: implement 'since' argument.
  user = service_util.get_or_create_user(users.get_current_user())

  if kwargs.has_key('gym_ids'):
    filtered_groups = filter(lambda x: x in group_ids, kwargs['group_ids'])

    query = Route.all().filter('groups IN', gym_ids)
#    if kwargs.has_key('since'):
#      query.filter('timestamp >=', service_util.get_datatime(kwargs['since']))
    query.order('-timestamp')

  else:
    raise jsonrpc.JsonRpcError('parameters', 'You must specify at least one '
                               'gym id.')

  return dict(routes=query.fetch(20, kwargs.get('offset', 0)))


if __name__ == '__main__':
  application = webapp.WSGIApplication([
        (config.get('SERVER_BASE_PATH', '') + '/rpc', jsonrpc.JsonRpcHandler)
      ],
      debug=('Development' in os.environ['SERVER_SOFTWARE'] or
             config.get('DEBUG')))
  wsgiref.handlers.CGIHandler().run(application)
