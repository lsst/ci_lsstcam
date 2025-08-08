from argparse import ArgumentParser
import os
import subprocess

from lsst.ci.builder import CommandRunner, BuildState, BaseCommand
from lsst.ci.builder.commands import (CreateButler, RegisterInstrument, WriteCuratedCalibrations,
                                      RegisterSkyMap, DefineVisits, ButlerImport,
                                      TestRunner)

TESTDATA_DIR = "/sdf/group/rubin/shared/data/test_data/testdata_ci_lsstcam_m49"
PRETRAINED_MODELS_DIR = "/sdf/group/rubin/shared/data/test_data/testdata_ci_imsim"
INSTRUMENT_NAME = "LSSTCam"
QGRAPH_FILE = "DRP.qgraph"
INPUTCOL = "LSSTCam/ci_m49,pretrained_models/tac_cnn_comcam_2025-02-18,skymaps"
COLLECTION = f"{INSTRUMENT_NAME}/runs/ci_lsstcam"
HIPS_COLLECTION = f"{INSTRUMENT_NAME}/runs/ci_lsstcam_hips"
SKYMAP = 'lsst_cells_v1'

index_command = 0

ciRunner = CommandRunner(os.environ["CI_LSSTCAM_DIR"])
ciRunner.register("butler", 0)(CreateButler)


@ciRunner.register("instrument", index_command := index_command + 1)
class LSSTCamRegisterInstrument(RegisterInstrument):
    instrumentName = "lsst.obs.lsst.LsstCam"


@ciRunner.register("write_calibrations", index_command := index_command + 1)
class LSSTCamWriteCuratedCalibrations(WriteCuratedCalibrations):
    instrumentName = INSTRUMENT_NAME


ciRunner.register("skymap", index_command := index_command + 1)(RegisterSkyMap)


@ciRunner.register("import_external", index_command := index_command + 1)
class LSSTCamBaseButlerImport(ButlerImport):
    dataLocation = TESTDATA_DIR

    @property
    def importFileLocation(self) -> str:
        return os.path.join(self.runner.pkgRoot, "resources", "external.yaml")


@ciRunner.register("define_visits", index_command := index_command + 1)
class LSSTCamDefineVisits(DefineVisits):
    instrumentName = INSTRUMENT_NAME
    collectionsName = f"{INSTRUMENT_NAME}/raw/all"


@ciRunner.register("import_external_pretrained_models", index_command := index_command + 1)
class LSSTCamButlerImportPretrainedModels(ButlerImport):
    dataLocation = PRETRAINED_MODELS_DIR

    @property
    def importFileLocation(self) -> str:
        return os.path.join(self.runner.pkgRoot, "resources", "external_pretrained_models.yaml")


@ciRunner.register("qgraph", index_command := index_command + 1)
class QgraphCommand(BaseCommand):
    @classmethod
    def addArgs(cls, parser: ArgumentParser):
        parser.add_argument("--config-no-limit-deblend", dest="no_limit_deblend", action="store_true",
                            help="Whether to disable useCiLimits for deblending and process all blends")
        parser.add_argument("--config-process-singles", dest="process_singles", action="store_true",
                            help="Whether to enable processSingles (isolated objects) for deblending")

    def run(self, currentState: BuildState):
        args = (
            "--long-log",
            "qgraph",
            "-d", f"skymap='{SKYMAP}' AND tract=10563 AND patch=36",
            "-b", self.runner.RunDir,
            "--input", INPUTCOL,
            "--output", COLLECTION,
            "-p", "$DRP_PIPE_DIR/pipelines/LSSTCam/DRP-ci_lsstcam.yaml",
            "--skip-existing",
            "--save-qgraph", os.path.join(self.runner.RunDir, QGRAPH_FILE),
            "--config", f"reprocessVisitImage:deblend.useCiLimits={not self.arguments.no_limit_deblend}",
            "--config",
            f"deblendCoaddFootprints:multibandDeblend.processSingles={self.arguments.process_singles}",
            "--config",
            f"deblendCoaddFootprints:multibandDeblend.useCiLimits={not self.arguments.no_limit_deblend}",
        )
        pipetask = self.runner.getExecutableCmd("CTRL_MPEXEC_DIR", "pipetask", args)
        subprocess.run(pipetask, check=True)


@ciRunner.register("process", index_command := index_command + 1)
class ProcessingCommand(BaseCommand):
    def run(self, currentState: BuildState):
        args = (
            "--long-log",
            "run",
            "-j", str(self.arguments.num_cores),
            "-b", self.runner.RunDir,
            "--input", INPUTCOL,
            "--output", COLLECTION,
            "--register-dataset-types",
            "--skip-existing",
            "--qgraph", os.path.join(self.runner.RunDir, QGRAPH_FILE),
        )
        pipetask = self.runner.getExecutableCmd("CTRL_MPEXEC_DIR", "pipetask", args)
        subprocess.run(pipetask, check=True)


@ciRunner.register("hips", index_command := index_command + 1)
class HipsGenerateCommand(BaseCommand):
    def run(self, currentState: BuildState):
        hipsDir = os.path.join(self.runner.RunDir, "hips")
        args = (
            "--long-log",
            "run",
            "-j", str(self.arguments.num_cores),
            "-b", self.runner.RunDir,
            "-i", COLLECTION,
            "--output", HIPS_COLLECTION,
            "-p", "$CI_LSSTCAM_DIR/resources/hips.yaml",
            "-c", "generateHips:hips_base_uri="+hipsDir,
            "-c", "generateColorHips:hips_base_uri="+hipsDir,
            "--register-dataset-types"
        )
        pipetask = self.runner.getExecutableCmd("CTRL_MPEXEC_DIR", "pipetask", args)
        subprocess.run(pipetask, check=True)


ciRunner.register("test", index_command := index_command + 1)(TestRunner)

ciRunner.run()
