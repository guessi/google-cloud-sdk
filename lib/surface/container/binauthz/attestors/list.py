# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""List attestors command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import authorities
from googlecloudsdk.api_lib.container.binauthz import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import util as cli_util


class List(base.ListCommand):
  """List Attestation Authorities associated with the current project."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(cli_util.ATTESTATION_AUTHORITY_LIST_FORMAT)

  def Run(self, args):
    return authorities.Client(apis.V1_BETA1).List(util.GetProjectRef())
