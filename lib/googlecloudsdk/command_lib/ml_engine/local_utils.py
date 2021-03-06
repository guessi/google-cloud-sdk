# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Utilities for local ml-engine operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import subprocess

from googlecloudsdk.command_lib.ml_engine import local_predict
from googlecloudsdk.command_lib.ml_engine import predict_utilities
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


class InvalidInstancesFileError(core_exceptions.Error):
  pass


class LocalPredictRuntimeError(core_exceptions.Error):
  """Indicates that some error happened within local_predict."""
  pass


class LocalPredictEnvironmentError(core_exceptions.Error):
  """Indicates that some error happened within local_predict."""
  pass


class InvalidReturnValueError(core_exceptions.Error):
  """Indicates that the return value from local_predict has some error."""
  pass


def RunPredict(model_dir, json_instances=None, text_instances=None,
               framework='tensorflow'):
  """Run ML Engine local prediction."""
  instances = predict_utilities.ReadInstancesFromArgs(json_instances,
                                                      text_instances)
  sdk_root = config.Paths().sdk_root
  if not sdk_root:
    raise LocalPredictEnvironmentError(
        'You must be running an installed Cloud SDK to perform local '
        'prediction.')
  # Inheriting the environment preserves important variables in the child
  # process. In particular, LD_LIBRARY_PATH under linux and PATH under windows
  # could be used to point to non-standard install locations of CUDA and CUDNN.
  # If not inherited, the child process could fail to initialize Tensorflow.
  env = os.environ.copy()
  env['CLOUDSDK_ROOT'] = sdk_root
  # We want to use whatever the user's Python was, before the Cloud SDK started
  # changing the PATH. That's where Tensorflow is installed.
  python_executables = files.SearchForExecutableOnPath('python')
  # Need to ensure that ml_sdk is in PYTHONPATH for the import in
  # local_predict to succeed.
  orig_py_path = ':' + env.get('PYTHONPATH') if env.get('PYTHONPATH') else ''
  env['PYTHONPATH'] = (os.path.join(sdk_root, 'lib', 'third_party', 'ml_sdk') +
                       orig_py_path)
  if not python_executables:
    # This doesn't have to be actionable because things are probably beyond help
    # at this point.
    raise LocalPredictEnvironmentError(
        'Something has gone really wrong; we can\'t find a valid Python '
        'executable on your PATH.')
  # Use python found on PATH or local_python override if set
  python_executable = (properties.VALUES.ml_engine.local_python.Get() or
                       python_executables[0])
  # Start local prediction in a subprocess.
  proc = subprocess.Popen(
      [python_executable, local_predict.__file__,
       '--model-dir', model_dir, '--framework', framework],
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
      env=env)

  # Pass the instances to the process that actually runs local prediction.
  for instance in instances:
    proc.stdin.write(json.dumps(instance) + '\n')
  proc.stdin.flush()

  # Get the results for the local prediction.
  output, err = proc.communicate()
  if proc.returncode != 0:
    raise LocalPredictRuntimeError(err)
  if err:
    log.warning(err)

  try:
    return json.loads(output)
  except ValueError:
    raise InvalidReturnValueError('The output for prediction is not '
                                  'in JSON format: ' + output)
