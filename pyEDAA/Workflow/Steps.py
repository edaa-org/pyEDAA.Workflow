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
from os import chdir
from pathlib import Path
from typing import List

from pyTooling.Decorators import export

from pyEDAA.Workflow.Workflow import Step, ExchangeObject as _ExchangeObject, Host, Workflow


@export
class ReadConfiguration(Step):
	pass


@export
class CreateProject(Step):
	pass


@export
class PurgeDirectories(Step):
	class ExchangeObject(_ExchangeObject):
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "PurgeDirectories", input: _ExchangeObject):
			super().__init__(step, input)

			self._deletedDirectoryItems = []

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

		@property
		def DeletedDirectoryItems(self) -> List[Path]:
			return self._deletedDirectoryItems

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)

	def _RunEnteringConsoleMessage(self) -> None:
		pass # self.LogDebug(f"Purging temporary directory: {self.Directories.Working}")

	def _Run(self) -> None:
		workingDirectory: Path = self._input["WorkingDirectory"]
		for item in workingDirectory.iterdir():
			self._output._deletedDirectoryItems.append(item)
			try:
				if item.is_dir():
					print(f"{'  '*self._host.level}  Deleting directory '{item}'")
					# shutil.rmtree(str(item))
				elif item.is_file():
					print(f"{'  '*self._host.level}  Deleting file '{item}'")
					# item.unlink()
			except OSError as ex:
				raise CommonException("Error while deleting '{0!s}'.".format(item)) from ex
		else:
			print(f"{'  '*self._host.level}  Working directory '{workingDirectory}' is already clean.")


@export
class CreateDirectory(Step):
	def _PrepareOutput(self) -> None:
		self._output = self._input

	def _RunEnteringConsoleMessage(self) -> None:
		pass # self.LogDebug("Creating temporary directory: {0!s}".format(self.Directories.Working))

	def _Run(self) -> None:
		workingDirectory: Path = self._input["WorkingDirectory"]
		try:
			workingDirectory.mkdir(parents=True)
			print(f"{'  '*self._host.level}  Creating working directory '{workingDirectory}'.")
		except OSError as ex:
			raise CommonException(f"Error while creating '{self.Directories.Working}'.") from ex


@export
class ChangeDirectory(Step):
	def _PrepareOutput(self) -> None:
		self._output = self._input

	def _RunEnteringConsoleMessage(self) -> None:
		pass # self.LogVerbose("Changing working directory to temporary directory.")

	def _Run(self) -> None:
		"""Change working directory to temporary path 'temp/<tool>'."""
		# self.LogDebug(f"cd \"{self.Directories.Working}\"")
		workingDirectory: Path = self._input["WorkingDirectory"]
		print(f"{'  '*self._host.level}  Changing working directory to '{workingDirectory}'.")
		try:
			chdir(workingDirectory)
		except OSError as ex:
			raise CommonException("Error while changing to '{0!s}'.".format(self.Directories.Working)) from ex


@export
class PrepareEnvironment(Step):
	_purgeStep: PurgeDirectories
	_createStep: CreateDirectory
	_cdStep: ChangeDirectory

	class ExchangeObject(_ExchangeObject):
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "PrepareEnvironment", input: _ExchangeObject):
			super().__init__(step, input)

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

	def __init__(self, name: str, host: "Host", workflow: "Workflow" = None, previousStep: "Step" = None):
		super().__init__(name, host, workflow, previousStep)

		self._purgeStep = PurgeDirectories(f"{name} - purge directory", host, self)
		self._createStep = CreateDirectory(f"{name} - create directory", host, self)
		self._cdStep = ChangeDirectory(f"{name} - change directory", host, self)

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)

	def _RunEnteringConsoleMessage(self) -> None:
		pass #self.LogVerbose("Creating a fresh temporary directory.")

	def _Run(self) -> None:
		self._host.level += 1

		if self._input["WorkingDirectory"].exists():
			step = self._purgeStep
		else:
			step = self._createStep

		step.Input = self._input
		step.Initialize()
		step.Run()

		self._cdStep.Input = self._input # step.Output
		self._cdStep.Initialize()
		self._cdStep.Run()

		self._host.level -= 1

		self._output = self._cdStep.Output


@export
class CreateLibrary(Step):
	class ExchangeObject(_ExchangeObject):
		_input: _ExchangeObject
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "CreateLibrary", input: _ExchangeObject):
			super().__init__(step, input)
			self._input = input

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)


@export
class MapLibrary(Step):
	class ExchangeObject(_ExchangeObject):
		_input: _ExchangeObject
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "MapLibrary", input: _ExchangeObject):
			super().__init__(step, input)
			self._input = input

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)


@export
class Analyze(Step):
	class ExchangeObject(_ExchangeObject):
		_input: _ExchangeObject
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "Analyze", input: _ExchangeObject):
			super().__init__(step, input)
			self._input = input

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)


@export
class Elaborate(Step):
	class ExchangeObject(_ExchangeObject):
		_input: _ExchangeObject
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "Elaborate", input: _ExchangeObject):
			super().__init__(step, input)
			self._input = input

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)


@export
class Simulate(Step):
	class ExchangeObject(_ExchangeObject):
		_input: _ExchangeObject
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "Simulate", input: _ExchangeObject):
			super().__init__(step, input)
			self._input = input

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)


@export
class View(Step):
	class ExchangeObject(_ExchangeObject):
		_input: _ExchangeObject
		_workingDirectory: Path
		_deletedDirectoryItems: List[Path]

		def __init__(self, step: "View", input: _ExchangeObject):
			super().__init__(step, input)
			self._input = input

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def WorkingDirectory(self) -> Path:
			return self._workingDirectory

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self, self._input)
