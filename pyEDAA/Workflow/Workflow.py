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
from typing import List, Optional as Nullable, Dict, Any, Type, TypeVar, Generic

from pyTooling.Decorators import export


@export
class Timer:
	_start: int
	_end: int

	def __init__(self):
		pass

	def Start(self):
		pass

	def Stop(self):
		pass

	@property
	def Duration(self):
		return None


T = TypeVar("T")

@export
class Parameter(Generic[T]):
	_obj: T

	def __init__(self, obj: T):
		self._obj = obj

	@property
	def Value(self) -> T:
		return self._obj

	def __str__(self) -> str:
		return str(self._obj)

	def __repr__(self) -> str:
		return repr(self._obj)


@export
class GlobalParameter(Parameter):
	pass


@export
class CopyParameter(Parameter):
	pass


@export
class ExchangeObject:
	_step: "Step"
	_input: "ExchangeObject"
	_dict: Dict[str, Parameter]
	_stream: Any
	_streamObjectType: Type

	def __init__(self, step: "Step", input: "ExchangeObject"):
		self._step = step
		self._input = input
		self._dict = {}

		if input is not None:
			for key, value in input._dict.items():
				if isinstance(value, GlobalParameter):
					self._dict[key] = value
				elif isinstance(value, CopyParameter):
					self._dict[key] = CopyParameter(value.Value)
				elif isinstance(value, ExchangeObject):
					self._dict[key] = value

			if input._step is not None:
				self._dict[input._step._name] = input

	def __getitem__(self, key: str) -> Any:
		return self._dict[key].Value

	def __setitem__(self, key: str, value: Any) -> None:
		if isinstance(value, Parameter):
			self._dict[key] = value
		else:
			self._dict[key] = GlobalParameter(value)

	@property
	def Input(self) -> "ExchangeObject":
		return self._input

	@property
	def Stream(self):
		return self._stream

	@property
	def StreamObject(self) -> Type:
		return self._streamObjectType


@export
class Result:
	pass


@export
class Step:
	_name: str
	_host: "Host"
	_workflow: "Workflow"
	_previousStep: Nullable["Step"]
	_nextStep: Nullable["Step"]
	_timer: "Timer"
	_input: Nullable[ExchangeObject]
	_output: ExchangeObject
	_result: Result

	def __init__(self, name: str, host: "Host", workflow: "Workflow" = None, previousStep: "Step" = None):
		self._name = name
		self._host = host
		self._workflow = workflow
		self._timer = Timer()
		self._previousStep = previousStep
		self._nextStep = None
		self._input = None

	@property
	def Name(self) -> str:
		return self._name

	@property
	def Workflow(self) -> Nullable["Workflow"]:
		return self._workflow

	@Workflow.setter
	def Workflow(self, value: "Workflow") -> None:
		self._workflow = value

	@property
	def PreviousStep(self) -> Nullable["Step"]:
		return self._previousStep

	@PreviousStep.setter
	def PreviousStep(self, value: "Step") -> None:
		self._previousStep = value

	@property
	def NextStep(self) -> Nullable["Step"]:
		return self._nextStep

	@NextStep.setter
	def NextStep(self, value: "Step") -> None:
		self._nextStep = value

	@property
	def Input(self) -> ExchangeObject:
		return self._input

	@Input.setter
	def Input(self, value: ExchangeObject) -> None:
		self._input = value

	@property
	def Output(self) -> ExchangeObject:
		return self._output

	def Initialize(self):
		self._PrepareOutput()

	def _PrepareOutput(self):
		raise NotImplementedError()

	def Run(self):
		print(f"{'  '*self._host.level}Executing step '{self._name}' ...")
		for key,value in self._input._dict.items():
			print(f"{'  '*self._host.level}  > {(key + ':'):20} {value}")
		print(f"{'  ' * self._host.level}  {'-'*120}")

		self._RunEntering()
		self._RunEnteringConsoleMessage()
		self._Run()
		self._RunLeavingConsoleMessage()
		self._RunLeaving()

		print(f"{'  ' * self._host.level}  {'-'*120}")
		for key,value in self._output._dict.items():
			print(f"{'  '*self._host.level}  < {(key + ':'):20} {value}")

	def _RunEntering(self):
		self._timer.Start()

	def _RunEnteringConsoleMessage(self):
		pass

	def _Run(self):
		pass

	def _RunLeavingConsoleMessage(self):
		pass

	def _RunLeaving(self):
		self._timer.Stop()

	def _AssembleOutput(self):
		pass

	def __str__(self):
		return self._name


@export
class Workflow:
	_name: str
	_host: "Host"
	_steps: List[Step]
	_initialStep: Step
	_input: Nullable[ExchangeObject]
	_output: ExchangeObject

	def __init__(self, name: str, host: "Host", steps: List[Step] = None):
		self._name = name
		self._host = host
		self._steps = []
		self._initialStep = None
		self._input = None
		self._output = ExchangeObject

		if steps is not None:
			iterator = iter(steps)
			try:
				previousStep = next(iterator)
				self._steps.append(previousStep)
				self._initialStep = previousStep
			except:
				return

			for step in iterator:
				step.PreviousStep = previousStep
				self._steps.append(step)
				previousStep = step

	@property
	def Input(self) -> ExchangeObject:
		return self._input

	@Input.setter
	def Input(self, value: ExchangeObject) -> None:
		self._input = value

	@property
	def Output(self) -> ExchangeObject:
		return self._output

	def AppendSteps(self, steps: List[Step]) -> None:
		iterator = iter(steps)
		try:
			previousStep = next(iterator)
			self._steps.append(previousStep)
			if self._initialStep is None:
				self._initialStep = previousStep
		except:
			return

		for step in iterator:
			step.PreviousStep = previousStep
			previousStep.NextStep = step
			self._steps.append(step)
			previousStep = step

	def Initialize(self):
		pass

	def Run(self):
		input: ExchangeObject = self._input
		step = self._initialStep

		print(f"{'  '*self._host.level}Running workflow '{self._name}' ...")
		for key,value in input._dict.items():
			print(f"{'  '*self._host.level}  > {(key + ':'):20} {value}")
		print(f"{'  ' * self._host.level}  {'=' * 120}")

		self._host.level += 1
		while step is not None:
			step.Input = input
			step.Initialize()
			step.Run()
			input = step.Output

			step = step.NextStep

		self._host.level -= 1
		self._output = input

		print(f"{'  ' * self._host.level}  {'=' * 120}")
		for key,value in input._dict.items():
			print(f"{'  '*self._host.level}  < {(key + ':'):20} {value}")

	def __str__(self):
		return self._name


@export
class Host:
	level = 0
