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

"""9a data models."""

__author__ = 'wes.goodman@gmail.com (Wes Goodman)'

import datetime
import pickle

from google.appengine.api import users
from google.appengine.ext import db

import util

class Climber(db.Model):
#  user_id = db.StringProperty()  # compare to users.User.user_id()
  user = db.UserProperty(auto_current_user_add=True)
  name = db.StringProperty()
  email = db.EmailProperty()

  EDITABLE_FIELDS = set(['name', 'email'])

  def json(self):
    return dict(user_id=self.user_id,
                email=self.email,
                name=self.name)

  @staticmethod
  def from_appengine_user(user):
    if not isinstance(user, users.User):
      raise TypeError("user must be a google.appengine.api.users.User")
    climber = Climber.all().filter('user =', user).get()
    if not climber:
      climber = Climber(user=user, name=user.nickname(), email=user.email())
      climber.put()
    return climber
#    return Climber(key_name=user.user_id(),
##                   user_id=user.user_id(),
#                   user=user,
#                   email=user.email(),
#                   name=user.nickname())


class Gym(db.Model):
  name = db.StringProperty()
  icon = db.LinkProperty(required=False)

  def _get_gym_id(self):
    return str(self.key().id())
  gym_id = property(_get_gym_id)

  def json(self):
    member_user_ids = [m.climber.user_id for m in self.memberships]
    owner_user_ids = [m.climber.user_id for m in self.memberships if m.owner]
    return dict(gym_id=self.gym_id,
                name=self.name,
                icon=self.icon,
                member_user_ids=member_user_ids,
                owner_user_ids=owner_user_ids)


class GymMembership(db.Model):
  climber = db.ReferenceProperty(Climber, collection_name='memberships')
  user = db.UserProperty(auto_current_user_add=True)
  gym = db.ReferenceProperty(Gym, collection_name='memberships')
  owner = db.BooleanProperty(default=False)


class Route(db.Model):
  author = db.ReferenceProperty(Climber, collection_name='created_routes')
  user = db.UserProperty(auto_current_user_add=True)
  gym = db.ReferenceProperty(Gym, collection_name='gym_routes')
  name = db.StringProperty()
  type = db.StringProperty()
  grade = db.StringProperty()
  description = db.TextProperty()
  extra = util.PickleProperty()
  timestamp = db.DateTimeProperty(auto_now_add=True)


class Send(db.Model):
  climber = db.ReferenceProperty(Climber, collection_name='sends')
  user = db.UserProperty(auto_current_user_add=True)
  route = db.ReferenceProperty(Route, collection_name='sends')
  gym = db.ReferenceProperty(Gym, collection_name='sends')
  timestamp = db.DateTimeProperty(auto_now_add=True)


class Comment(db.Model):
  route = db.ReferenceProperty(Route, collection_name='comments')
  author = db.ReferenceProperty(Climber, collection_name='authored_comments')
  user = db.UserProperty(auto_current_user_add=True)
  body = db.TextProperty()
  extra = util.PickleProperty()
  timestamp = db.DateTimeProperty(auto_now_add=True)
