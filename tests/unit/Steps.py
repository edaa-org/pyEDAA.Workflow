from typing import List
from unittest import TestCase

from pyEDAA.Workflow.Workflow import Step


class TestStep(Step):
	collector: List = []

	def __init__(self, collector):
		super().__init__("Test", "TestStep", self)
		self.collector = collector

	def _PrepareOutput(self):
		self.collector.append(0)

	def _RunEntering(self):
		self.collector.append(1)

	def _RunEnteringConsoleMessage(self):
		self.collector.append(2)

	def _Run(self):
		self.collector.append(3)

	def _RunLeavingConsoleMessage(self):
		self.collector.append(4)

	def _RunLeaving(self):
		self.collector.append(5)


class Steps(TestCase):
	def test_Step(self):
		collector = []
		step = TestStep(collector)
		step.Initialize()
		step.Run()

		self.assertEqual("Test", step.Name)
		self.assertEqual("TestStep", step.Description)
		self.assertListEqual([0, 1, 2, 3, 4, 5], step.collector)
