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
"""Unt tests for ``Step`` classes."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict
from unittest import TestCase

import colorama

from pyEDAA.Workflow        import Workflow, Host, ExchangeObject as _ExchangeObject
from pyEDAA.Workflow.Steps  import CreateProject as _CreateProject, PrepareEnvironment, CreateLibrary, Analyze, Elaborate, Simulate, View


@dataclass
class Project:
	Name: str
	Libraries: Dict[str, List[Path]]


class CreateProject(_CreateProject):
	class ExchangeObject(_ExchangeObject):
		_project: Project

		def __init__(self, name: str, step: "CreateProject", input: _ExchangeObject):
			super().__init__(name, step, input)
			self._project = Project("StopWatch", {})

			self["WorkingDirectory"] = input["WorkingDirectory"]
			self["Project"] = self._project

		@property
		def Input(self) -> _ExchangeObject:
			return self._input

		@property
		def Project(self) -> Project:
			return self._project

	def _PrepareOutput(self) -> None:
		self._output = self.ExchangeObject(self.__class__.__name__, self, self._input)

	def _RunEnteringConsoleMessage(self) -> None:
		pass # self.LogDebug(f"Purging temporary directory: {self.Directories.Working}")

	def _Run(self) -> None:
		if "Project" not in self._output:
			raise Exception()

		project: Project = self._output["Project"]
		project.Libraries["lib1"] = [
			Path("file1.vhdl"),
			Path("file2.vhdl"),
			Path("file3.vhdl")
		]
		project.Libraries["lib2"] = [
			Path("file11.vhdl"),
			Path("file12.vhdl")
		]
		print(f"{'  ' * self._host.level}  - Project: {project.Name}")
		for lib, files in project.Libraries.items():
			print(f"{'  ' * self._host.level}      {lib}")
			for file in files:
				print(f"{'  ' * self._host.level}        {file}")


class Simulation(TestCase):
	def test_MainFlow(self):
		print()

		colorama.init()

		host = Host()
		workflow = Workflow("MainFlow", "test flow", host)

		steps = [
			CreateProject("GenerateProject", "generate project", host, workflow),
			PrepareEnvironment("PrepareEnvironment", "prepare environment", host, workflow),
			CreateLibrary("CreateLibrary", "create library", host, workflow),
			Analyze("Analyze", "analyze", host, workflow),
			Elaborate("Elaborate", "elaborate", host, workflow),
			Simulate("Simulate", "simulate", host, workflow),
			View("View", "view", host, workflow)
		]
		workflow.AppendSteps(steps)

		input = _ExchangeObject("Initial", None, None)
		input["WorkingDirectory"] = Path("temp")
		input["ProjectFile"] = Path("project.xpr")

		workflow.Input = input
		workflow.Initialize()
		workflow.Run()
		output = workflow.Output
