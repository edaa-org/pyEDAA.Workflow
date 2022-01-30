from time import sleep
from unittest import TestCase

from pyEDAA.Workflow.Workflow import Timer as _Timer, GlobalParameter, CopyParameter, LocalParameter, ExchangeObject as _ExchangeObject

class Parameter(TestCase):
	def test_GlobalParameter(self):
		value = 15
		parameter = GlobalParameter(value)

		self.assertEqual(value, parameter.Value)
		self.assertEqual(str(value), str(parameter))
		self.assertEqual(repr(value), repr(parameter))

	def test_CopyParameter(self):
		value = 15
		parameter = CopyParameter(value)

		self.assertEqual(value, parameter.Value)
		self.assertEqual(str(value), str(parameter))
		self.assertEqual(repr(value), repr(parameter))

	def test_LocalParameter(self):
		value = 15
		parameter = LocalParameter(value)

		self.assertEqual(value, parameter.Value)
		self.assertEqual(str(value), str(parameter))
		self.assertEqual(repr(value), repr(parameter))


class Timer(TestCase):
	def test_StartStop(self):
		timer = _Timer()
		timer.Start()
		sleep(1)
		timer.Stop()
		delay = timer.DurationInSec

		self.assertLess(delay, 1.002)
		self.assertLess(1.0, delay)

	def test_StartStopShort(self):
		timer = _Timer().Start()
		sleep(1)
		delay = timer.Stop()

		self.assertLess(delay, 1.002)
		self.assertLess(1.0, delay)


class ExchangeObject(TestCase):
	def test_ExchangeObject(self):
		eo = _ExchangeObject("Test", None, None)
		eo["int"] = 25

		self.assertEqual(25, eo["int"])
		self.assertIn("int", eo)
		for key, value in eo:
			if key == "int":
				self.assertEqual(25, value.Value)
				break
		else:
			self.assertTrue(False)
