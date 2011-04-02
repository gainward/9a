#!/usr/bin/python2.5
#
# Copyright 2009
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

"""9a web client handlers."""

__author__ = 'wes.goodman@gmail.com (Wes Goodman)'

import os
from os import path
import wsgiref.handlers

from models import Climber
from models import Gym
from models import GymMembership
from models import Send

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.template import render


#template.register_template_library(
#    'django.contrib.humanize.templatetags.humanize')
#template.register_template_library('templatelib')
#
#
#def make_static_handler(template_file):
#  """Creates a webapp.RequestHandler type that renders the given template
#  to the response stream."""
#  class StaticHandler(webapp.RequestHandler):
#    def get(self):
#      self.response.out.write(template.render(
#          os.path.join(os.path.dirname(__file__), template_file),
#          {'current_user': users.get_current_user()}))
#
#  return StaticHandler


class MainHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    sends = []
    if user:
      member_gyms = [i.gym for i in Climber.from_appengine_user(user).memberships.fetch(20)]
      sends = [gym.sends.order('-timestamp').fetch(20) for gym in member_gyms]
    else:
      sends = Send.all().order('-timestamp').fetch(20)
    context = {
        'user': user,
#        'login': users.create_login_url(self.request.uri),
        'login': users.create_login_url('/login'),
        'logout': users.create_logout_url(self.request.uri),
        'sends': sends}
    tmpl = path.join(path.dirname(__file__), 'static/html/index.html')
    self.response.out.write(render(tmpl, context))


class LoginHandler(MainHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      climber = Climber.from_appengine_user(user)
    super(LoginHandler, self).get()

class GymHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      context = {
          'user': user,
          'logout': users.create_logout_url(self.request.uri)}
    else:
      context = {
          'login': users.create_login_url('/login')}
    context['gyms'] = [Gym.all().fetch(20)]
    tmpl = path.join(path.dirname(__file__), 'static/html/gyms.html')
    self.response.out.write(render(tmpl, context))


class AddGymHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      context = {
          'user': user,
#          'login': users.create_login_url(self.request.uri),
          'login': users.create_login_url('/login'),
          'logout': users.create_logout_url(self.request.uri)}
    else:
      context = {
#          'login': users.create_login_url(self.request.uri),
          'login': users.create_login_url('/login'),
          'error': 'log in to create a gym!'}
    tmpl = path.join(path.dirname(__file__), 'static/html/addgym.html')
    self.response.out.write(render(tmpl, context))

  def post(self):
    user = users.get_current_user()
    if user:
      climber = Climber.from_appengine_user(user)
      gym = Gym()
      gym.name = self.request.get('name')
      gym.put()

      membership = GymMembership()
      membership.climber = climber
      membership.user = user
      membership.gym = gym
      membership.owner = True
      membership.put()

      context = {
          'gym_name': gym.name,
          'error': False}
    else:
      context = {'error': 'log in to create a gym!'}

    tmpl = path.join(path.dirname(__file__), 'static/html/addgymresult.html')
    self.response.out.write(render(tmpl, context))


class MembershipHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    context = {
        'user': user,
        'login': users.create_login_url('/login'),
        'logout': users.create_logout_url(self.request.uri)}
    if user:
      climber = Climber.from_appengine_user(user)
      memberships = climber.memberships.fetch(20)
      context['memberships'] = memberships
    else:
      context['error'] = 'log in to view memberships!'
    tmpl = path.join(path.dirname(__file__), 'static/html/memberships.html')
    self.response.out.write(render(tmpl, context))


class AdminHandler(webapp.RequestHandler):
  def get(self):
    gyms = Gym.all().getch(20)
    context = {
      'gyms': gyms}
    tmpl = path.join(path.dirname(__file__), 'static/html/admin.html')
    self.response.out.write(render(tmpl, context))


class GymAdder(webapp.RequestHandler):
  def post(self):
    gym = Gym()
    gym.name = self.request.get('name')
    gym.put()
    self.redirect('/')

class RouteAdder(webapp.RequestHandler):
  def post(self):
    route = Route()
    route.author = self.request.get('author')
    route.gym = self.request.get('gym')
    route.name = self.request.get('name')
    route.type = self.request.get('type')
    route.grade = self.request.get('grade')
    route.description = self.request.get('description')
    route.put()
    self.redirect('/')


def main():
  application = webapp.WSGIApplication([
      # ('/', make_static_handler('templates/index.html')),
      ('/', MainHandler), ('/gyms', GymHandler), ('/addgym', AddGymHandler),
      ('/addroute', RouteAdder), ('/login', LoginHandler),
      ('/memberships', MembershipHandler)
      ],
      debug=('Development' in os.environ['SERVER_SOFTWARE']))
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
