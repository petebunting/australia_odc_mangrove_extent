# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OzMangroveChangeViewer
                                 A QGIS plugin
 Allows for viewing of changes in mangrove extent around Australia.
                             -------------------
        begin                : 2018-01-18
        copyright            : (C) 2018 by Pete Bunting
        email                : pete.bunting@aber.ac.uk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load OzMangroveChangeViewer class from file OzMangroveChangeViewer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .ozmangchangeview import OzMangroveChangeViewer
    return OzMangroveChangeViewer(iface)
