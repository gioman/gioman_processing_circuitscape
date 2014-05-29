# -*- coding: utf-8 -*-

"""
***************************************************************************
    CircuitscapeProvider.py
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

from PyQt4.QtGui import *

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from processing.tools import system

from processing_circuitscape.Pairwise import Pairwise
from processing_circuitscape.OneToAll import OneToAll
from processing_circuitscape.CircuitscapeUtils import CircuitscapeUtils


class CircuitscapeProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = False

        self.alglist = [Pairwise(), OneToAll()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

        if system.isWindows():
            ProcessingConfig.addSetting(Setting(self.getDescription(),
                CircuitscapeUtils.CIRCUITSCAPE_FOLDER,
                'Circuitscape folder',
                CircuitscapeUtils.circuitscapePath()))

        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.FOUR_NEIGHBOURS,
            'Connect raster cells to four neighbors instead of eight',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.AVERAGE_CONDUCTANCE,
            'Use average conductance instead of resistance for connections between cells',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.PREEMPT_MEMORY,
            'Preemptively release memory when possible',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.LOG_TRANSFORM,
            'Log-transform current maps',
            False))
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            CircuitscapeUtils.COMPRESS_OUTPUT,
            'Compress output grids',
            False))

    def unload(self):
        AlgorithmProvider.unload(self)

        if system.isWindows():
            ProcessingConfig.removeSetting(CircuitscapeUtils.CIRCUITSCAPE_FOLDER)

        ProcessingConfig.removeSetting(CircuitscapeUtils.FOUR_NEIGHBOURS)
        ProcessingConfig.removeSetting(CircuitscapeUtils.AVERAGE_CONDUCTANCE)
        ProcessingConfig.removeSetting(CircuitscapeUtils.PREEMPT_MEMORY)
        ProcessingConfig.removeSetting(CircuitscapeUtils.LOG_TRANSFORM)

    def getName(self):
        return 'Circuitscape'

    def getDescription(self):
        return 'Circuitscape'

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/circuitscape.png')

    def _loadAlgorithms(self):
        self.algs = self.alglist
