# -*- coding: utf-8 -*-

"""
***************************************************************************
    Circuitscape.py
    ---------------------
    Date                 : May 2014
    Copyright            : (C) 2014 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'May 2014'
__copyright__ = '(C) 2014, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import ConfigParser

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

from processing.core.Processing import Processing
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException

from processing.parameters.ParameterSelection import ParameterSelection
from processing.parameters.ParameterRaster import ParameterRaster
from processing.parameters.ParameterBoolean import ParameterBoolean
from processing.parameters.ParameterString import ParameterString
from processing.outputs.OutputDirectory import OutputDirectory

from processing.tools import system

from CircuitscapeUtils import CircuitscapeUtils


class Circuitscape(GeoAlgorithm):

    MODE = 'MODE'
    RESISTANCE_MAP = 'RESISTANCE_MAP'
    IS_CONDUCTANCES = 'IS_CONDUCTANCES'
    FOCAL_NODE = 'FOCAL_NODE'
    WRITE_CURRENT_MAP = 'WRITE_CURRENT_MAP'
    WRITE_VOLTAGE_MAP = 'WRITE_VOLTAGE_MAP'
    BASENAME = 'BASENAME'
    DIRECTORY = 'DIRECTORY'

    MODES = ['Pairwise',
             'One to all',
             'All to one'
            ]
    MODES_DICT = {0: 'pairwise',
                  1: 'one-to-all',
                  2: 'all-to-one'
                 }

    def defineCharacteristics(self):
        self.name = 'Circuitscape (simple mode)'
        self.group = 'Circuitscape'

        self.addParameter(ParameterSelection(self.MODE,
            'Modelling mode', self.MODES, 0))
        self.addParameter(ParameterRaster(self.RESISTANCE_MAP,
            'Raster resistance map'))
        self.addParameter(ParameterBoolean(self.IS_CONDUCTANCES,
            'Data represent conductances instead of resistances', False))
        self.addParameter(ParameterRaster(self.FOCAL_NODE,
            'Focal node location'))
        self.addParameter(ParameterBoolean(self.WRITE_CURRENT_MAP,
            'Create current map', True))
        self.addParameter(ParameterBoolean(self.WRITE_VOLTAGE_MAP,
            'Create voltage map', True))
        self.addParameter(ParameterString(self.BASENAME,
            'Output basename', 'csoutput'))

        self.addOutput(OutputDirectory(self.DIRECTORY, 'Output directory'))

    def processAlgorithm(self, progress):
        if system.isWindows():
            path = CircuitscapeUtils.CircuitscapePath()
            if path == '':
                raise GeoAlgorithmExecutionException(
                    'Circuitscape folder is not configured.\nPlease '
                    'configure it before running Circuitscape algorithms.')

        mode = self.MODES_DICT[self.getParameterValue(self.MODE)]
        resistance = self.getParameterValue(self.RESISTANCE_MAP)
        useConductance = str(not self.getParameterValue(self.IS_CONDUCTANCES))
        focal = self.getParameterValue(self.FOCAL_NODE)
        writeCurrent = str(self.getParameterValue(self.WRITE_CURRENT_MAP))
        writeVoltage = str(self.getParameterValue(self.WRITE_VOLTAGE_MAP))

        baseName = self.getParameterValue(self.BASENAME)
        directory = self.getOutputValue(self.DIRECTORY)
        progress.setInfo('basename: %s' % baseName)
        progress.setInfo('directory: %s' % directory)

        basePath = os.path.join(directory, baseName)

        iniPath = CircuitscapeUtils.writeConfiguration()
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(iniPath)

        # set parameters
        cfg.set('Circuitscape mode', 'scenario', mode)

        cfg.set('Habitat raster or graph', 'habitat_map_is_resistances', useConductance)
        cfg.set('Habitat raster or graph', 'habitat_file', resistance)

        cfg.set('Options for pairwise and one-to-all and all-to-one modes', 'point_file', focal)

        cfg.set('Output options', 'write_cur_maps', writeCurrent)
        cfg.set('Output options', 'write_volt_maps', writeVoltage)
        cfg.set('Output options', 'output_file', basePath)

        # write configuration back to file
        with open(iniPath, 'wb') as f:
          cfg.write(f)

        if system.isWindows():
            commands = [os.path.join(path, 'csrun.exe'), iniPath]
        else:
            commands = ['csrun.py', iniPath]

        CircuitscapeUtils.executeCircuitscape(commands, progress)
