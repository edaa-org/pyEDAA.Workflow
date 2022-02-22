from pathlib import Path
from typing import List, cast
from unittest import TestCase

from anytree import PostOrderIter

from pyEDAA.ToolSetup.Interface import HDLSimulator
from pyEDAA.ToolSetup.OpenSource.GHDL import GHDLInstance
from pyVHDLModel import VHDLVersion
from pyEDAA.CLITool.GHDL import GHDL
from pyEDAA.ProjectModel import Project, FileSet, VHDLSourceFile, VHDLLibrary
from pyEDAA.ToolSetup import Installations
from pyEDAA.ToolSetup.DataModel import Installation, Vendor, Tool, ToolInstance
from pyEDAA.Workflow import Workflow, ExchangeObject, Host
from pyEDAA.Workflow.Steps import PrepareEnvironment, CreateLibrary as _CreateLibrary


class CreateAndAnalyzeLibrary(_CreateLibrary):
	def _RunEnteringConsoleMessage(self):
		libraryName: str = self._input["VHDLLibrary"]
		print(f"Creating and analyzing toplevel VHDL library '{libraryName}' ...")

	def _Run(self):
		project: Project = self._input["Project"]
		toplevelLibraryName: str = self._input["VHDLLibrary"]

		design = project.DefaultDesign
		toplevelLibrary = design.VHDLLibraries[toplevelLibraryName]

		for library in PostOrderIter(toplevelLibrary):
			self._CreateLibraryDirectory(library)
			self._AnalyzeLibrary(library)

	def _CreateLibraryDirectory(self, library: VHDLLibrary) -> None:
		print(f"  Creating subdirectory for the library '{library.Name}' ...")

	def _AnalyzeLibrary(self, library: VHDLLibrary) -> None:
		hdlSimulator: HDLSimulator = self._input["HDLSimulator"]
		analyzer: GHDL = cast(GHDL, hdlSimulator.GetVHDLAnalyzer())
		analyzer[analyzer.FlagVHDlStandard] = VHDLVersion.VHDL2008
		analyzer[analyzer.FlagLibrary] = library.Name
		analyzer[analyzer.FlagRelaxed] = True
		analyzer[analyzer.FlagExplicit] = True
		analyzer[analyzer.FlagMultiByteComments] = True
		analyzer[analyzer.FlagSynopsys] = True

		analyzer[analyzer.OptionPath] = Path(".")

		print(f"  Analyzing VHDL files into VHDL library '{library.Name}'")
		for file in library.Files:
			analyzer[analyzer.OptionPath].Value = file.ResolvedPath

			arguments = analyzer.ToArgumentList()

			print(f"    Analyzing VHDL file '{file}'")
			print(f"      {arguments}")


class Analyze(TestCase):
	def _CreateProject(self) -> Project:
		# Create a Project by code
		project = Project("ghdl", rootDirectory=Path("src"), vhdlVersion=VHDLVersion.VHDL2008)
		dutLibrary = VHDLLibrary("design", project=project)
		dutFileset = FileSet("design", project=project)
		dutFileset.AddFiles([
			VHDLSourceFile(Path("counter.vhdl"), vhdlLibrary=dutLibrary),
			VHDLSourceFile(Path("toplevel.vhdl"), vhdlLibrary=dutLibrary),
		])

		testLibrary = VHDLLibrary("test", project=project)
		testLibrary.AddDependency(dutLibrary)
		testFileset = FileSet("testbench", project=project)
		testFileset.AddFiles([
			VHDLSourceFile(Path("testbench.vhdl"), vhdlLibrary=testLibrary),
		])

		return project

	def _CreateWorkflow(self, host) -> Workflow:
		# Create a workflow
		workflow = Workflow("ghdl", "Analyze source files", host)
		steps = [
			#		CreateProject("GenerateProject", "generate project", host, workflow),
			PrepareEnvironment("PrepareEnvironment", "prepare environment", host, workflow),
			CreateAndAnalyzeLibrary("AnalyzeLibrary", "create and analyze library", host, workflow),
			# Elaborate("Elaborate", "elaborate", host, workflow),
			# Simulate("Simulate", "simulate", host, workflow),
			#	View("View", "view", host, workflow)
		]
		workflow.AppendSteps(steps)

		return workflow

	def test_FromPATH(self):
		pass

	def test_ManualConfiguration(self):
		installation = Installation()
		vendor = Vendor("OpenSource", Path(r"C:\Tools"), parent=installation)
		tool = Tool("ghdl", parent=vendor)
		version = "2.0.0.dev0-mingw32-mcode"
		installationPath = vendor.InstallationDirectory / "GHDL" / version
		binaryPath = installationPath / "bin"
		ghdlInstallationInstance = ToolInstance(installationPath, binaryPath, version, parent=tool)

		project = self._CreateProject()

		host = Host()
		workflow = self._CreateWorkflow(host)
		input = ExchangeObject("Initial", None, None)
		input["WorkingDirectory"] = Path("temp").resolve()
		input["Project"] = project
		input["VHDLLibrary"] = "test"
		input["HDLSimulator"] = ghdlInstallationInstance

		workflow.Input = input
		workflow.Run()

	def test_FromConfigByDefault(self):
		installationsFile = Path(r"tests/integration/configuration.yml")
		installations = Installations(installationsFile)
		ghdlInstallations = installations["OpenSource"]["GHDL"]
		ghdlInstallationInstance = ghdlInstallations.Default

		project = self._CreateProject()

		host = Host()
		workflow = self._CreateWorkflow(host)
		input = ExchangeObject("Initial", None, None)
		input["WorkingDirectory"] = Path("temp").resolve()
		input["Project"] = project
		input["VHDLLibrary"] = "test"
		input["HDLSimulator"] = ghdlInstallationInstance
		workflow.Input = input
		workflow.Run()

	def test_FromConfigByExplicitVariant(self):
		installationsFile = Path(r"tests/integration/configuration.yml")
		installations = Installations(installationsFile)
		ghdlInstallations = installations["OpenSource"]["GHDL"]
		ghdlInstallationInstance: GHDLInstance = ghdlInstallations["2.0.0.dev0-mingw32-mcode"]

		project = self._CreateProject()

		host = Host()
		workflow = self._CreateWorkflow(host, project, ghdlInstallationInstance)
		workflow.Input = input
		workflow.Run()
