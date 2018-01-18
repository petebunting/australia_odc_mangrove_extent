# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OzMangroveChangeViewerDialog
                                 A QGIS plugin
 Allows for viewing of changes in mangrove extent around Australia.
                             -------------------
        begin                : 2018-01-18
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Pete Bunting
        email                : pete.bunting@aber.ac.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtCore, QtGui
import qgis.utils
import numpy

class OzMangroveChangeViewerDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        """Constructor."""
        QtGui.QWidget.__init__(self, parent)
        # Set window size. 
        self.resize(320, 240)

        # Set window title  
        self.setWindowTitle("Accuracy Assessment Tool") 
        
        # Create mainLayout
        self.mainLayout = QtGui.QVBoxLayout()
        
        self.guiLabelStep1 = QtGui.QLabel()
        self.guiLabelStep1.setText("1. Select a Vector Layer:")
        self.mainLayout.addWidget(self.guiLabelStep1)
        
        self.availLayersCombo = QtGui.QComboBox()
        self.availLayersCombo.currentIndexChanged['QString'].connect(self.populateLayerInfo)
        self.mainLayout.addWidget(self.availLayersCombo)
        
        self.guiLabelStep2 = QtGui.QLabel()
        self.guiLabelStep2.setText("2. Select Grid ID Column:")
        self.mainLayout.addWidget(self.guiLabelStep2)
        
        self.GridIDColComboLabel = QtGui.QLabel()
        self.GridIDColComboLabel.setText("Grid ID Column:")
        self.GridIDColCombo = QtGui.QComboBox()
        self.GridIDColLayout = QtGui.QHBoxLayout()
        self.GridIDColLayout.addWidget(self.GridIDColComboLabel)
        self.GridIDColLayout.addWidget(self.GridIDColCombo)
        self.mainLayout.addLayout(self.GridIDColLayout)
        
        self.guiLabelStep3 = QtGui.QLabel()
        self.guiLabelStep3.setText("3. Press Run When Polys Selected:")
        self.mainLayout.addWidget(self.guiLabelStep3)
        
        self.runButton = QtGui.QPushButton(self)
        self.runButton.setText("Run")
        self.runButton.setDefault(True)
        self.connect(self.runButton, QtCore.SIGNAL("clicked()"), self.runProcessing)
        
        self.mainButtonLayout = QtGui.QHBoxLayout()
        self.mainButtonLayout.addWidget(self.runButton)
        self.mainLayout.addLayout(self.mainButtonLayout)
        
        self.guiLabelStep4 = QtGui.QLabel()
        self.guiLabelStep4.setText("4. List of Selected Tiles:")
        self.mainLayout.addWidget(self.guiLabelStep4)
        
        self.outTextBox = QtGui.QTextEdit()
        self.mainTextOutLayout = QtGui.QHBoxLayout()
        self.mainTextOutLayout.addWidget(self.outTextBox)
        self.mainLayout.addLayout(self.mainTextOutLayout)
        
        self.setLayout(self.mainLayout)
    
    def populateLayers(self):
        """ Initialise layers list """
        self.availLayersCombo.clear()
        self.GridIDColCombo.clear()
        
        qgisIface = qgis.utils.iface
        mCanvas = qgisIface.mapCanvas()
        
        allLayers = mCanvas.layers()
        first = True
        for layer in allLayers:
            self.availLayersCombo.addItem(layer.name())
                    
    def populateLayerInfo(self, selectedName):
        """ Populate the layer information from the selected layer """
        self.GridIDColCombo.clear()
        
        qgisIface = qgis.utils.iface
        mCanvas = qgisIface.mapCanvas()
        
        allLayers = mCanvas.layers()
        found = False
        fieldNames = list()
        for layer in allLayers:
            if layer.name() == selectedName:
                layerFields = layer.pendingFields()
                numFields = layerFields.size()
                for i in range(numFields):
                    field = layerFields.field(i)
                    if field not in fieldNames:
                        self.GridIDColCombo.addItem(field.name())
                        fieldNames.append(field)
                found = True
                break

    
    def runProcessing(self):
        """ Run Processing """
        qgisIface = qgis.utils.iface
                    
        mCanvas = qgisIface.mapCanvas()
        
        selectedIdx = self.availLayersCombo.currentIndex()
        selectedName = self.availLayersCombo.itemText(selectedIdx)
        
        selGridIDFieldIdx = self.GridIDColCombo.currentIndex()
        selGridIDFieldName = self.GridIDColCombo.itemText(selGridIDFieldIdx)
        
        cFeatLayer = None
        
        allLayers = mCanvas.layers()
        found = False
        for layer in allLayers:
            if layer.name() == selectedName:
                cFeatLayer = layer
                break
        
        selectFeats = cFeatLayer.selectedFeatures()
        if len(selectFeats) > 0:
            gridIDArr = []
            for cFeat in selectFeats:
                gridIDArr.append(int(cFeat[selGridIDFieldName]))
            print(gridIDArr)
            
            
            self.outTextBox.setPlainText(str(gridIDArr))










