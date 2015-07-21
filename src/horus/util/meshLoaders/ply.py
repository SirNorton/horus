# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------#
#                                                                       #
# This file is part of the Horus Project                                #
#                                                                       #
# Copyright (C) 2014-2015 Mundo Reader S.L.                             #
#                                                                       #
# Date: June 2014                                                       #
# Author: Jesús Arroyo Torrens <jesus.arroyo@bq.com>                    #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 2 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                       #
#-----------------------------------------------------------------------#

"""
PLY file point cloud loader.

	- Binary, which is easy and quick to read.
	- Ascii, which is harder to read, as can come with windows, mac and unix style newlines.

This module also contains a function to save objects as an PLY file.

http://en.wikipedia.org/wiki/PLY_(file_format)
"""

__author__ = "Jesús Arroyo Torrens <jesus.arroyo@bq.com>"
__license__ = "GNU General Public License v2 http://www.gnu.org/licenses/gpl.html"

import os
import struct
import numpy as np

from horus.util import model

def _loadAscii(mesh, stream, dtype, count):
	fields = dtype.fields

	v = 0
	c = 0

	if 'c' in fields:
		c += 3
	if 'n' in fields:
		c += 3

	i = 0
	while i < count:
		i += 1
		data = stream.readline().split(' ')
		if data is not None:
			mesh._addVertex(data[v],data[v+1],data[v+2],data[c],data[c+1],data[c+2])

def _loadBinary(mesh, stream, dtype, count):
	data = np.fromfile(stream, dtype=dtype , count=count)

	fields = dtype.fields
	mesh.vertexCount = count

	if 'v' in fields:
		mesh.vertexes = data['v']
	else:
		mesh.vertexes = np.zeros((count,3))

	if 'n' in fields:
		mesh.normal = data['n']
	else:
		mesh.normal = np.zeros((count,3))

	if 'c' in fields:
		mesh.colors = data['c']
	else:
		mesh.colors = 255 * np.ones((count,3))

def loadScene(filename):
	obj = model.Model(filename, isPointCloud=True)
	m = obj._addMesh()
	with open(filename, "rb") as f:
		dtype = []
		count = 0
		format = None
		line = None
		header = ''

		while line != 'end_header\n' and line != '':
			line = f.readline()
			header += line
		#-- Discart faces
		header = header.split('element face ')[0].split('\n')

		if header[0] == 'ply':

			for line in header:
				if 'format ' in line:
					format = line.split(' ')[1]
					break

			if format is not None:
				if format == 'ascii':
					fm = ''
				elif format == 'binary_big_endian':
					fm = '>'
				elif format == 'binary_little_endian':
					fm = '<'

			df = {'float' : fm+'f', 'uchar' : fm+'B'}
			dt = {'x' : 'v', 'nx' : 'n', 'red' : 'c', 'alpha' : 'a'}
			ds = {'x' : 3, 'nx' : 3, 'red' : 3, 'alpha' : 1}

			for line in header:
				if 'element vertex ' in line:
					count = int(line.split('element vertex ')[1])
				elif 'property ' in line:
					props = line.split(' ')
					if props[2] in dt.keys():
						dtype = dtype + [(dt[props[2]], df[props[1]], (ds[props[2]],))]

			dtype = np.dtype(dtype)

			if format is not None:
				if format == 'ascii':
					m._prepareVertexCount(count)
					_loadAscii(m, f, dtype, count)
				elif format == 'binary_big_endian' or format == 'binary_little_endian':
					_loadBinary(m, f, dtype, count)
			obj._postProcessAfterLoad()
			return obj

		else:
			print "Error: incorrect file format."
			return None

def saveScene(filename, _object):
	with open(filename, 'wb') as f:
		saveSceneStream(f, _object)

def saveSceneStream(stream, _object):
	m = _object._mesh

	binary = True

	if m is not None:
		frame  = "ply\n"
		if binary:
			frame += "format binary_little_endian 1.0\n"
		else:
			frame += "format ascii 1.0\n"
		frame += "comment Generated by Horus software\n"
		frame += "element vertex {0}\n".format(m.vertexCount)
		frame += "property float x\n"
		frame += "property float y\n"
		frame += "property float z\n"
		frame += "property uchar red\n"
		frame += "property uchar green\n"
		frame += "property uchar blue\n"
		frame += "element face 0\n"
		frame += "property list uchar int vertex_indices\n"
		frame += "end_header\n"
		stream.write(frame)
		if m.vertexCount > 0:
			if binary:
				for i in xrange(m.vertexCount):
					stream.write(struct.pack("<fffBBB", m.vertexes[i,0], m.vertexes[i,1], m.vertexes[i,2] , m.colors[i,0], m.colors[i,1], m.colors[i,2]))
			else:
				for i in xrange(m.vertexCount):
					stream.write("{0} {1} {2} {3} {4} {5}\n".format(m.vertexes[i,0], m.vertexes[i,1], m.vertexes[i,2] , m.colors[i,0], m.colors[i,1], m.colors[i,2]))