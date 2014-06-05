# -*- coding: utf-8 -*-

"""
***************************************************************************
    Advanced.py
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
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException

from processing.parameters.ParameterRaster import ParameterRaster
from processing.parameters.ParameterBoolean import ParameterBoolean
from processing.parameters.ParameterSelection import ParameterSelection
from processing.parameters.ParameterString import ParameterString
from processing.parameters.ParameterFile import ParameterFile
from processing.outputs.OutputDirectory import OutputDirectory

from processing.tools import system

from CircuitscapeUtils import CircuitscapeUtils

sessionExportedLayers = {}


class Advanced(GeoAlgorithm):

    RESISTANCE_MAP = 'RESISTANCE_MAP'
    IS_CONDUCTANCES = 'IS_CONDUCTANCES'
    CURRENT_SOURCE = 'CURRENT_SOURCE'
    GROUND_POINT = 'GROUND_POINT'
    GP_CONDUCTANCES = 'GP_CONDUCTANCES'
    MODE = 'MODE'
    UNIT_CURRENTS = 'UNIT_CURRENTS'
    DIRECT_CONNECTIONS = 'DIRECT_CONNECTIONS'
    WRITE_CURRENT_MAP = 'WRITE_CURRENT_MAP'
    WRITE_VOLTAGE_MAP = 'WRITE_VOLTAGE_MAP'
    MASK = 'MASK'
    SHORT_CIRCUIT = 'SHORT_CIRCUIT'
    BASENAME = 'BASENAME'
    DIRECTORY = 'DIRECTORY'

    MODES = ['Keep both when possible but remove ground if source is tied directly to ground',
             'Remove source',
             'Remove ground',
             'Remove both source and ground'
            ]
    MODES_DICT = {0: 'keepall',
                  1: 'rmvsrc',
                  2: 'rmvgnd',
                  3: 'rmvall'
                 }

    def defineCharacteristics(self):
        self.name = 'Advanced modelling'
        self.group = 'Circuitscape'

        self.addParameter(ParameterRaster(self.RESISTANCE_MAP,
            'Raster resistance map'))
        self.addParameter(ParameterBoolean(self.IS_CONDUCTANCES,
            'Data represent conductances instead of resistances', False))
        self.addParameter(ParameterRaster(self.CURRENT_SOURCE,
            'Current source file'))
        self.addParameter(ParameterRaster(self.GROUND_POINT,
            'Ground point file'))
        self.addParameter(ParameterBoolean(self.GP_CONDUCTANCES,
            'Data represent conductances instead of resistances to ground', False))
        self.addParameter(ParameterSelection(self.MODE,
            'When a source and ground are at the same node', self.MODES, 0))
        self.addParameter(ParameterBoolean(self.UNIT_CURRENTS,
            'Use unit currents (i = 1) for all current sources', False))
        self.addParameter(ParameterBoolean(self.DIRECT_CONNECTIONS,
            'Use direct connections to ground (R = 0) for all ground points', False))
        self.addParameter(ParameterBoolean(self.WRITE_CURRENT_MAP,
            'Create current map', True))
        self.addParameter(ParameterBoolean(self.WRITE_VOLTAGE_MAP,
            'Create voltage map', True))
        self.addParameter(ParameterRaster(self.MASK,
            'Raster mask file', optional=True))
        self.addParameter(ParameterRaster(self.SHORT_CIRCUIT,
            'Raster short-circuit region file', optional=True))
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

        resistance = self.getParameterValue(self.RESISTANCE_MAP)
        useConductance = str(not self.getParameterValue(self.IS_CONDUCTANCES))
        currentSources = self.getParameterValue(self.CURRENT_SOURCE)
        groundPoints = self.getParameterValue(self.GROUND_POINT)
        gpConductance = str(not self.getParameterValue(self.GP_CONDUCTANCES))

        writeCurrent = str(self.getParameterValue(self.WRITE_CURRENT_MAP))
        writeVoltage = str(self.getParameterValue(self.WRITE_VOLTAGE_MAP))

        # advanced parameters
        mode = self.MODES_DICT[self.getParameterValue(self.MODE)]
        unitCurrents = str(self.getParameterValue(self.UNIT_CURRENTS))
        directConnections = str(self.getParameterValue(self.DIRECT_CONNECTIONS))
        mask = self.getParameterValue(self.MASK)
        shortCircuit = self.getParameterValue(self.SHORT_CIRCUIT)

        baseName = self.getParameterValue(self.BASENAME)
        directory = self.getOutputValue(self.DIRECTORY)
        progress.setInfo('basename: %s' % baseName)
        progress.setInfo('directory: %s' % directory)

        basePath = os.path.join(directory, baseName)

        iniPath = CircuitscapeUtils.writeConfiguration()
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(iniPath)

        commands = []
        self.exportedLayers = {}
        for param in self.parameters:
            if isinstance(param, ParameterRaster):
                if param.value is None:
                    continue
                value = param.value
                if not value.lower().endswith('asc'):
                    exportCommand = self.exportRasterLayer(value)
                    if exportCommand is not None:
                        commands.append(exportCommand)

        # set parameters
        cfg.set('Circuitscape mode', 'scenario', 'advanced')

        cfg.set('Habitat raster or graph', 'habitat_map_is_resistances', useConductance)
        if resistance in self.exportedLayers.keys():
            resistance = self.exportedLayers[resistance]
        cfg.set('Habitat raster or graph', 'habitat_file', resistance)

        if currentSources in self.exportedLayers.keys():
            currentSources = self.exportedLayers[currentSources]
        cfg.set('Options for advanced mode', 'source_file', currentSources)
        if groundPoints in self.exportedLayers.keys():
            groundPoints = self.exportedLayers[groundPoints]
        cfg.set('Options for advanced mode', 'ground_file', groundPoints)
        cfg.set('Options for advanced mode', 'ground_file_is_resistances', gpConductance)
        cfg.set('Options for advanced mode', 'remove_src_or_gnd', unitCurrents)
        cfg.set('Options for advanced mode', 'use_direct_grounds', directConnections)

        if mask is not None:
            if mask in self.exportedLayers.keys():
                mask = self.exportedLayers[mask]
            cfg.set('Mask file', 'mask_file', mask)
            cfg.set('Mask file', 'use_mask', 'True')

        if shortCircuit is not None:
            if shortCircuit in self.exportedLayers.keys():
                shortCircuit = self.exportedLayers[shortCircuit]
            cfg.set('Short circuit regions (aka polygons)', 'polygon_file', shortCircuit)
            cfg.set('Short circuit regions (aka polygons)', 'use_polygons', 'True')

        cfg.set('Output options', 'write_cur_maps', writeCurrent)
        cfg.set('Output options', 'write_volt_maps', writeVoltage)
        cfg.set('Output options', 'output_file', basePath)

        # write configuration back to file
        with open(iniPath, 'wb') as f:
          cfg.write(f)

        if system.isWindows():
            commands.append(os.path.join(path, 'csrun.exe') + ' ' + iniPath)
        else:
            commands.append('csrun.py ' + iniPath)

        CircuitscapeUtils.createBatchJobFileFromCommands(commands)
        loglines = []
        loglines.append('Circuitscape execution commands')
        for line in commands:
            progress.setCommand(line)
            loglines.append(line)

        if ProcessingConfig.getSetting(CircuitscapeUtils.LOG_COMMANDS):
            ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)

        CircuitscapeUtils.executeCircuitscape(commands, progress)

    def exportRasterLayer(self, source):
        global sessionExportedLayers

        if source in sessionExportedLayers:
            self.exportedLayers[source] = sessionExportedLayers[source]
            return None

        fileName = os.path.basename(source)
        validChars = \
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:'
        fileName = ''.join(c for c in fileName if c in validChars)
        if len(fileName) == 0:
            fileName = 'layer'

        destFilename = system.getTempFilenameInTempFolder(fileName + '.asc')
        self.exportedLayers[source] = destFilename
        sessionExportedLayers[source] = destFilename

        return 'gdal_translate -of AAIGrid %s %s' % (source, destFilename)
