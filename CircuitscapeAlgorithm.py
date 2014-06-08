# -*- coding: utf-8 -*-

"""
***************************************************************************
    CircuitscapeAlgorithm.py
    ---------------------
    Date                 : June 2014
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
__date__ = 'June 2014'
__copyright__ = '(C) 2014, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

from processing.core.GeoAlgorithm import GeoAlgorithm

from processing.parameters.ParameterRaster import ParameterRaster

from processing.tools import system

from CircuitscapeUtils import CircuitscapeUtils

sessionExportedLayers = {}


class CircuitscapeAlgorithm(GeoAlgorithm):

    def __init__(self):
        GeoAlgorithm.__init__(self)

        self.exportedLayers = {}

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

    def prepareInputs(self):
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
        return commands
