# ==================================================================================================================== #
#              _____ ____    _        _  __        __         _     __ _                                               #
#  _ __  _   _| ____|  _ \  / \      / \ \ \      / /__  _ __| | __/ _| | _____      __                                #
# | '_ \| | | |  _| | | | |/ _ \    / _ \ \ \ /\ / / _ \| '__| |/ / |_| |/ _ \ \ /\ / /                                #
# | |_) | |_| | |___| |_| / ___ \  / ___ \ \ V  V / (_) | |  |   <|  _| | (_) \ V  V /                                 #
# | .__/ \__, |_____|____/_/   \_\/_/   \_(_)_/\_/ \___/|_|  |_|\_\_| |_|\___/ \_/\_/                                  #
# |_|    |___/                                                                                                         #
# ==================================================================================================================== #
# Authors:                                                                                                             #
#   Patrick Lehmann                                                                                                    #
#                                                                                                                      #
# License:                                                                                                             #
# ==================================================================================================================== #
# Copyright 2014-2022 Patrick Lehmann - Bötzingen, Germany                                                             #
#                                                                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");                                                      #
# you may not use this file except in compliance with the License.                                                     #
# You may obtain a copy of the License at                                                                              #
#                                                                                                                      #
#   http://www.apache.org/licenses/LICENSE-2.0                                                                         #
#                                                                                                                      #
# Unless required by applicable law or agreed to in writing, software                                                  #
# distributed under the License is distributed on an "AS IS" BASIS,                                                    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                             #
# See the License for the specific language governing permissions and                                                  #
# limitations under the License.                                                                                       #
#                                                                                                                      #
# SPDX-License-Identifier: Apache-2.0                                                                                  #
# ==================================================================================================================== #
#
"""Execution of EDA tools in a workflow."""
from pyTooling.Decorators import export

from pyEDAA.Workflow.Workflow import Step, Output


@export
class ReadConfiguration(Step):
	pass


@export
class CreateProject(Step):
	pass


class PurgeDirectories(Step):
	def _PrepareOutput(self):
		pass

	def _RunEnteringConsoleMessage(self):
		pass # self.LogDebug(f"Purging temporary directory: {self.Directories.Working}")

	def _Run(self):
		for item in range(0): # self.Directories.Working.iterdir():
			try:
				if item.is_dir():
					pass # shutil.rmtree(str(item))
				elif item.is_file():
					item.unlink()
			except OSError as ex:
				raise CommonException("Error while deleting '{0!s}'.".format(item)) from ex


class CreateDirectory(Step):
	def _PrepareOutput(self):
		pass

	def _RunEnteringConsoleMessage(self):
		pass # self.LogDebug("Creating temporary directory: {0!s}".format(self.Directories.Working))

	def _Run(self):
		try:
			self.Directories.Working.mkdir(parents=True)
		except OSError as ex:
			raise CommonException(f"Error while creating '{self.Directories.Working}'.") from ex


class ChangeDirectory(Step):
	def _PrepareOutput(self):
		pass

	def _RunEnteringConsoleMessage(self):
		pass # self.LogVerbose("Changing working directory to temporary directory.")

	def _Run(self):
		"""Change working directory to temporary path 'temp/<tool>'."""
		pass # self.LogDebug(f"cd \"{self.Directories.Working}\"")
		try:
			pass # chdir(str(self.Directories.Working))
		except OSError as ex:
			raise CommonException("Error while changing to '{0!s}'.".format(self.Directories.Working)) from ex


@export
class PrepareEnvironmentOutput(Output):
	pass


@export
class PrepareEnvironment(Step):
	_purgeStep: PurgeDirectories
	_createStep: CreateDirectory
	_cdStep: ChangeDirectory

	def __init__(self, name: str, host: "Host", workflow: "Workflow" = None, previousStep: "Step" = None):
		super().__init__(name, host, workflow, previousStep)

		self._purgeStep = PurgeDirectories(f"{name} - purge directory", host, self)
		self._createStep = CreateDirectory(f"{name} - create directory", host, self)
		self._cdStep = ChangeDirectory(f"{name} - change directory", host, self)

	def _PrepareOutput(self):
		self._output = PrepareEnvironmentOutput(self)

	def _RunEnteringConsoleMessage(self):
		pass #self.LogVerbose("Creating a fresh temporary directory.")

	def _Run(self):
		if (True): # self.Directories.Working.exists()):
			self._purgeStep.Run()
		else:
			self._createStep.Run()

		self._cdStep.Run()


@export
class CreateLibraryOutput(Output):
	pass


@export
class CreateLibrary(Step):
	def _PrepareOutput(self):
		self._output = CreateLibraryOutput(self)


@export
class MapLibraryOutput(Output):
	pass


@export
class MapLibrary(Step):
	def _PrepareOutput(self):
		self._output = MapLibraryOutput(self)


@export
class AnalyzeOutput(Output):
	pass


@export
class Analyze(Step):
	def _PrepareOutput(self):
		self._output = AnalyzeOutput(self)


@export
class ElaborateOutput(Output):
	pass


@export
class Elaborate(Step):
	def _PrepareOutput(self):
		self._output = ElaborateOutput(self)


@export
class SimulateOutput(Output):
	pass


@export
class Simulate(Step):
	def _PrepareOutput(self):
		self._output = SimulateOutput(self)


@export
class ViewOutput(Output):
	pass


@export
class View(Step):
	def _PrepareOutput(self):
		self._output = ViewOutput(self)
