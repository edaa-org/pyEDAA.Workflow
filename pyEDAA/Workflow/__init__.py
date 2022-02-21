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
__author__ =    "Patrick Lehmann"
__email__ =     "Paebbels@gmail.com"
__copyright__ = "2014-2022, Patrick Lehmann"
__license__ =   "Apache License, Version 2.0"
__version__ =   "0.1.0"
__keywords__ =  ["workflow", "management", "eda", "simulation", "synthesis"]

from enum import Enum
from time import time_ns
from typing import List, Optional as Nullable, Dict, Any, Type, TypeVar, Generic, Union, Iterator, Tuple

import colorama
from pyTooling.Decorators import export


@export
class Timer:
	_name: Nullable[str]
	_start: int
	_stop: int
	_delay: float

	def __init__(self, name: str = None):
		self._name = name

	def Start(self) -> "Timer":
		self._start = time_ns()
		return self

	def Stop(self) -> float:
		stop = time_ns()
		self._stop = stop
		self._delay = stop - self._start
		return self._delay / 1.0e9

	@property
	def DurationInMSec(self) -> float:
		return self._delay / 1.0e6

	@property
	def DurationInSec(self) -> float:
		return self._delay / 1.0e9


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
class LocalParameter(Parameter):
	pass


@export
class CopyParameter(Parameter):
	pass


@export
class ExchangeObject:
	_name: str
	_step: "Step"
	_input: "ExchangeObject"
	_dict: Dict[str, Union[Parameter, "ExchangeObject", None]]
	_stream: Any
	_streamObjectType: Type

	def __init__(self, name: str, step: Nullable["Step"], input: Nullable["ExchangeObject"]):
		self._name = name
		self._step = step
		self._input = input
		self._dict = {}

		if step is None:
			self._dict["Previous_Step"] = None
			self._dict["Previous_Input"] = None

		if input is not None:
			for key, value in input:
				if isinstance(value, GlobalParameter) or value is None:
					self._dict[key] = value
				elif isinstance(value, CopyParameter):
					self._dict[key] = CopyParameter(value.Value)
				elif isinstance(value, LocalParameter):
					pass # print(f"skipped '{key}'")
				elif isinstance(value, ExchangeObject):
					self._dict[key] = value
				else:
					raise Exception()

	def __iter__(self) -> Iterator[Tuple[str, Union[Parameter, "ExchangeObject"]]]:
		return iter(self._dict.items())

	def __contains__(self, key: str) -> bool:
		return key in self._dict

	def __getitem__(self, key: str) -> Any:
		return self._dict[key].Value

	def __setitem__(self, key: str, value: Any) -> None:
		if isinstance(value, Parameter):
			self._dict[key] = value
		else:
			self._dict[key] = GlobalParameter(value)

	@property
	def Name(self) -> str:
		return self._name

	@property
	def Input(self) -> "ExchangeObject":
		return self._input

	@property
	def PreviousStep(self) -> "Step":
		return self._previousStep

	@property
	def PreviousStepInput(self) -> "ExchangeObject":
		return self._previousStepInput

	@property
	def Stream(self):
		return self._stream

	@property
	def StreamObject(self) -> Type:
		return self._streamObjectType

	def __str__(self) -> str:
		return self._name


@export
class Result(Enum):
	Unknown = 0


@export
class Base:
	_name: str
	_description: str
	_host: "Host"
	_timer: "Timer"
	_input: Nullable[ExchangeObject]
	_output: Nullable[ExchangeObject]
	_result: Result

	def __init__(self, name: str, description: str, host: "Host"):
		self._name = name
		self._description = description
		self._host = host
		self._timer = Timer()
		self._input = None
		self._output = None
		self._result = Result.Unknown

	@property
	def Name(self) -> str:
		return self._name

	@property
	def Description(self) -> str:
		return self._description

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


@export
class Step(Base):
	_workflow: "Workflow"
	_previousStep: Nullable["Step"]
	_nextStep: Nullable["Step"]

	def __init__(self, name: str, description: str, host: "Host", workflow: "Workflow" = None, previousStep: "Step" = None):
		super().__init__(name, description, host)

		self._workflow = workflow
		self._previousStep = previousStep
		self._nextStep = None

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

	def Run(self):
		self._RunEntering()
		self._RunEnteringConsoleMessage()
		self._Run()
		self._RunLeavingConsoleMessage()
		self._RunLeaving()

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

	def __str__(self) -> str:
		return self._name


@export
class Workflow(Base):
	_steps: List[Step]
	_initialStep: Step

	def __init__(self, name: str, description: str, host: "Host", steps: List[Step] = None):
		super().__init__(name, description, host)

		self._steps = []
		self._initialStep = None

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

		print(f"{'  '*self._host.level}{colorama.Fore.CYAN}Running workflow '{self._name}' ...{colorama.Fore.RESET}")
		for key,value in input:
			print(f"{'  '*self._host.level}  > {(key + ':'):24} {value}")
		print(f"{'  ' * self._host.level}  {'=' * 120}")

		self._host.level += 1
		while step is not None:
			step.Input = input
			step.Initialize()
			step.Run()

			output = step.Output
			output["Previous_Step"] = step
			output["Previous_Input"] = input
			output["Previous_Output"] = output
			output[f"step_{step.Name}"] = output

			step = step.NextStep
			input = output

		self._host.level -= 1
		self._output = input

		print(f"{'  ' * self._host.level}  {'=' * 120}")
		for key,value in input:
			print(f"{'  '*self._host.level}  < {(key + ':'):24} {value}")

	def __str__(self):
		return self._name


@export
class Host:
	level = 0
