# This file is part of ci_lsstcam.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import unittest
import yaml

from lsst.daf.butler import Butler
import lsst.utils.tests

from lsst.utils import getPackageDir

BUTLER_DIR = os.path.join(getPackageDir("ci_lsstcam"), "DATA")
SCHEMA_FILE = os.path.join(getPackageDir("sdm_schemas"), "yml", "lsstcam.yaml")
COLLECTION = "LSSTCam/runs/ci_lsstcam"


class TestSchemaMatch(lsst.utils.tests.TestCase):
    """Check the schema of the parquet outputs match the DDL in sdm_schemas"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.butler = Butler(BUTLER_DIR, writeable=False, collections=COLLECTION)
        cls.skymap = list(cls.butler.registry.queryDatasets(datasetType="object"))[0].dataId["skymap"]
        with open(SCHEMA_FILE, "r") as f:
            cls.schema = yaml.safe_load(f)["tables"]

    def _validateSchema(self, dataset, dataId, tableName):
        """Check column name and data type match between dataset and DDL"""
        info = f"dataset={dataset} tableName={tableName} dataId={dataId}"

        sdmSchema = [table for table in self.schema if table["name"] == tableName]
        self.assertEqual(len(sdmSchema), 1)
        expectedColumns = {
            column["name"]: column["datatype"] for column in sdmSchema[0]["columns"]
        }

        df = self.butler.get(dataset, dataId, storageClass="DataFrame")
        df.reset_index(inplace=True)

        outputColumnNames = df.columns.to_list()

        # Edit expectedColumns and outputColumnNames per exceptions

        # 1. If there is no index col, pandas adds index col when reset_index
        if "index" in outputColumnNames:
            outputColumnNames.remove("index")
        if "index" in expectedColumns:
            expectedColumns.pop("index")

        # 2. Mag and MagErr are added in the view
        # and are not expected in parquet files
        expectedColumns = {k: v for k, v in expectedColumns.items() if not k.endswith(("Mag", "MagErr"))}

        # 3. Bands for non-existent data don't appear in DiaObject
        # and there is no z or y-band data in testdata_ci_lsstcam_m49
        if tableName == "DiaObject":
            expectedColumns = {k: v for k, v in expectedColumns.items() if not k.startswith(('z_', 'y_'))}

        # 4. forcedSourceId and forcedSourceOnDiaObjectId were removed in dp1
        outputColumnNames = [c for c in outputColumnNames
                             if c not in ('forcedSourceId', 'forcedSourceOnDiaObjectId')]



        self.assertEqual(
            set(outputColumnNames), set(expectedColumns.keys()), f"{info} failed"
        )

        # the data type mapping from felis datatype to pandas
        typeMapping = {
            "boolean": "^bool$",
            "short": "^int16$",
            "int": "^int32$",
            "long": "^int64$",
            "float": "^float32$",
            "double": "^float64$",
            "char": "^object$",
            "timestamp": r"^datetime64\[[un]s\]$",
        }
        for column in outputColumnNames:
            self.assertRegex(
                df.dtypes.get(column).name,
                typeMapping[expectedColumns[column]],
                f"{info} column={column} failed",
            )

    def testObjectSchemaMatch(self):
        """Check object table"""
        dataId = {"instrument": "LSSTCam", "tract": 10563, "skymap": self.skymap}
        self._validateSchema("object", dataId, "Object")

    def testSourceSchemaMatch(self):
        """Check one source table"""
        dataId = {
            "instrument": "LSSTCam",
            "detector": 148,
            "visit": 2025050300358,
        }
        self._validateSchema("source", dataId, "Source")

    def testForcedSourceSchemaMatch(self):
        """Check object_forced_source"""
        dataId = {
            "instrument": "LSSTCam",
            "tract": 10563,
            "patch": 36,
            "skymap": self.skymap,
        }
        self._validateSchema("object_forced_source", dataId, "ForcedSource")

    def testForcedSourceeOnDiaObjectSchemaMatch(self):
        """Check dia_object_forced_source"""
        dataId = {
            "instrument": "LSSTCam",
            "tract": 10563,
            "patch": 36,
            "skymap": self.skymap,
        }
        self._validateSchema(
            "dia_object_forced_source", dataId, "ForcedSourceOnDiaObject"
        )

    def testDiaObjectSchemaMatch(self):
        """Check dia_object"""
        dataId = {"instrument": "LSSTCam", "tract": 10563, "skymap": self.skymap}
        self._validateSchema("dia_object", dataId, "DiaObject")

    def testDiaSourceSchemaMatch(self):
        """Check one dia_source"""
        dataId = {"instrument": "LSSTCam", "tract": 10563, "skymap": self.skymap}
        self._validateSchema("dia_source", dataId, "DiaSource")


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
