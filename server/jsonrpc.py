# Copyright 2010 Roman Nurik
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

import decimal
import datetime
import logging
import time
import urllib

from django.utils import simplejson

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import config
import models


DEBUG = config.get('DEBUG', False)

RPC_METHODS = {}


def method(rpc_name):
  """Decorator for making a method callable via JSON RPC."""
  def __decorate__(fn):
    def __wrapper__(self, *args, **kwargs):
      return fn(self, *args, **kwargs)

    RPC_METHODS[rpc_name] = __wrapper__
    return __wrapper__
  return __decorate__


def require_login(fn):
  def __wrapper__(self, *args, **kwargs):
    if not users.get_current_user():
      raise JsonRpcError('auth.login_required',
                         'You must be logged in for this method.')
    return fn(self, *args, **kwargs)
  return __wrapper__  


class JsonRpcError(Exception):
  def __init__(self, error_code, message):
    self.error_code = error_code
    self.message = message

  def __str__(self):
    return "JsonRpcError: [%s] %s" % (self.error_code, self.message)


class JsonRpcHandler(webapp.RequestHandler):
  """Helper class for request handlers that return JSON."""

  def get(self):
    call = {}
    
    # Convert the flat request arguments into a [potentially nested] dict.
    try:
      for k in self.request.arguments():
        # See if the value for this key is an array
        v = self.request.get_all(k)
        if isinstance(v, list) and len(v) == 1:
          v = v[0]

        # See if this key is nested (i.e. ...&extra.location=foo)
        dest_obj = call
        if '.' in k:
          k_parts = k.split('.')
          for k_part in k_parts[:-1]:
            if not k_part in dest_obj:
              dest_obj[k_part] = {}
            dest_obj = dest_obj[k_part]
          k = k_parts[-1]
      
        dest_obj[k] = v
      
      responses = [self.rpc_call(call)]
    
    except TypeError, e:
      if DEBUG:
        raise
      responses = [dict(error='parameters',
                        message='Invalid method arguments.')]

    self.render(responses=responses)

  def post(self):
    responses = []
    
    request = None
    try:
      request = simplejson.loads(self.request.body)
    
    except ValueError, e:
      self.render(error='parse', message=e.message)
      return
    
    calls = request['calls'] if request.has_key('calls') else []
    for call in calls:
      responses.append(self.rpc_call(call))

    self.render(responses=responses)
  
  def rpc_call(self, call):
    try:
      if not call.has_key('method'):
        raise JsonRpcError('parameters', 'No method supplied.')
      elif not RPC_METHODS.has_key(call['method']):
        raise JsonRpcError('parameters', 'Invalid method.')
      
      # Lightly sanitize 'call' dictionary as method arguments dictionary
      non_arg_keys = set(['method', 'pretty'])
      args = {}
      for k in call.keys():
        if not k in non_arg_keys:
          args[str(k)] = call[k]
      
      response = dict(status='ok')
      data = RPC_METHODS[call['method']](self, **args)
      if data:
        response.update(data=data)
      return response

    except JsonRpcError, e:
      return dict(error=e.error_code, message=e.message)

    except TypeError, e:
      if DEBUG:
        raise
      return dict(error='parameters', message='Invalid method arguments.')

  def render(self, **kwargs):
    """Serializes the passed data from this request to JSON and outputs."""
    if self.request.get('pretty'):
      encoder = _DjangoJSONEncoder(indent=2, sort_keys=True)
    else:
      encoder = _DjangoJSONEncoder()
    
    self.response.headers.add_header('Content-Type', 'application/json')
    self.response.out.write(encoder.encode(kwargs) + '\n')


class _DjangoJSONEncoder(simplejson.JSONEncoder):
  """JSONEncoder subclass that knows how to encode date/time and decimal
  types. Borrowed and extended from Django:
  http://code.djangoproject.com/browser/django/trunk/django/core/serializers/json.py
  """
  DATE_FORMAT = "%Y-%m-%d"
  TIME_FORMAT = "%H:%M:%S"
  def default(self, o):
    if hasattr(o, 'json') and callable(getattr(o, 'json')):
      return o.json()
    if isinstance(o, datetime.datetime):
      return o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
    elif isinstance(o, datetime.date):
      return o.strftime(self.DATE_FORMAT)
    elif isinstance(o, datetime.time):
      return o.strftime(self.TIME_FORMAT)
    elif isinstance(o, decimal.Decimal):
      return str(o)
    else:
      return super(_DjangoJSONEncoder, self).default(o)
