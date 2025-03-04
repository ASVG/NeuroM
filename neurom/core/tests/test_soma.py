# Copyright (c) 2015, Ecole Polytechnique Federale de Lausanne, Blue Brain Project
# All rights reserved.
#
# This file is part of NeuroM <https://github.com/BlueBrain/NeuroM>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#     3. Neither the name of the copyright holder nor the names of
#        its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import math
import warnings
from io import StringIO

import numpy as np
from morphio import MorphioError, SomaError
from neurom import load_neuron
from neurom.core import _soma
from mock import Mock
from nose import tools as nt
from numpy.testing import assert_array_equal


def test_no_soma_builder():
    morphio_soma = Mock()
    morphio_soma.type = None
    nt.assert_raises(SomaError, _soma.make_soma, morphio_soma)
    try:
        _soma.make_soma(morphio_soma)
    except SomaError as e:
        nt.assert_in('No NeuroM constructor for MorphIO soma type', e.args[0])


def test_no_soma():
    sm = load_neuron(StringIO(u"""
        ((Dendrite)
        (0 0 0 1.0)
        (0 0 0 2.0))"""), reader='asc').soma
    nt.assert_is_none(sm.center)
    nt.eq_(sm.points.shape, (0, 4))


def test_Soma_SinglePoint():
    sm = load_neuron(StringIO(u"""1 1 11 22 33 44 -1"""), reader='swc').soma
    nt.ok_('SomaSinglePoint' in str(sm))
    nt.ok_(isinstance(sm, _soma.SomaSinglePoint))
    nt.eq_(list(sm.center), [11, 22, 33])
    nt.ok_(sm.radius == 44)


def test_Soma_contour():
    with warnings.catch_warnings(record=True):
        sm = load_neuron(StringIO(u"""((CellBody)
                                      (0 0 0 44)
                                      (0 -44 0 44)
                                      (0 +44 0 44))"""), reader='asc').soma

    nt.ok_('SomaSimpleContour' in str(sm))
    nt.ok_(isinstance(sm, _soma.SomaSimpleContour))
    nt.eq_(list(sm.center), [0, 0, 0])
    nt.assert_almost_equal(sm.radius, 29.33333333, places=5)


def test_Soma_ThreePointCylinder():
    sm = load_neuron(StringIO(u"""1 1 0   0 0 44 -1
                                  2 1 0 -44 0 44  1
                                  3 1 0 +44 0 44  1"""), reader='swc').soma
    nt.ok_('SomaNeuromorphoThreePointCylinders' in str(sm))
    nt.ok_(isinstance(sm, _soma.SomaNeuromorphoThreePointCylinders))
    nt.eq_(list(sm.center), [0, 0, 0])
    nt.eq_(sm.radius, 44)


def test_Soma_ThreePointCylinder_invalid_radius():
    with warnings.catch_warnings(record=True) as w_list:
        load_neuron(StringIO(u"""
                        1 1 0   0 0 1e-8 -1
                        2 1 0 -1e-8 0 1e-8  1
                        3 1 0 +1e-8 0 1e-8  1"""), reader='swc').soma
        nt.assert_in('Zero radius for SomaNeuromorphoThreePointCylinders', str(w_list[0]))


def test_Soma_ThreePointCylinder_invalid():
    swc_content = StringIO(u"""
                        1 1 0   0 0 1e-8 -1
                        2 1 0 -44 0 1e-8  1
                        3 1 0 +44 0 1e-8  1""")
    nt.assert_raises(MorphioError, load_neuron, swc_content, reader='swc')
    try:
        load_neuron(swc_content, reader='swc')
    except MorphioError as e:
        nt.assert_in('Warning: the soma does not conform the three point soma spec', e.args[0])


def check_SomaC(stream):
    sm = load_neuron(StringIO(stream), reader='asc').soma
    nt.ok_('SomaSimpleContour' in str(sm))
    nt.ok_(isinstance(sm, _soma.SomaSimpleContour))
    np.testing.assert_almost_equal(sm.center, [0., 0., 0.])
    nt.assert_almost_equal(sm.radius, 1.0)


def test_SomaC():
    with warnings.catch_warnings(record=True):
        check_SomaC(u"""((CellBody)
                        (1 0 0 44)
                        (0 1 0 44)
                        (-1 0 0 44)
                        (0 -1 0 44)) """)

        sin_pi_by_4 = math.cos(math.pi/4.)
        cos_pi_by_4 = math.sin(math.pi/4.)

        check_SomaC(u"""((CellBody)
                         (1 0 0 44)
                         ({sin} {cos} 0 44)
                         (0 1 0 44)
                         (-1 0 0 44)
                         (-{sin} -{cos} 0 44)
                         (0 -1 0 44))""".format(sin=sin_pi_by_4,
                                                cos=cos_pi_by_4))

        check_SomaC(u"""((CellBody)
        (1 0 0 44)
        ({sin} {cos} 0 44)
        (0 1 0 44)
        (-{sin} {cos} 0 44)
        (-1 0 0 44)
        (-{sin} -{cos} 0 44)
        (0 -1 0 44)
        ({sin} -{cos} 0 44))""".format(sin=sin_pi_by_4,
                                       cos=cos_pi_by_4))


def test_soma_points_2():
    load_neuron(StringIO(u"""
                    1 1 0 0 -10 40 -1
                    2 1 0 0   0 40  1"""), reader='swc').soma
    load_neuron(StringIO(u"""((CellBody)
                             (0 0 0 44)
                             (0 +44 0 44))"""), reader='asc').soma


def test_Soma_Cylinders():
    s = load_neuron(StringIO(u"""
                1 1 0 0 -10 40 -1
                2 1 0 0   0 40  1
                3 1 0 0  10 40  2"""), reader='swc').soma

    # if r = 2*h (ie: as in this case 10 - -10 == 20), then the
    # area of a cylinder (excluding end caps) is:
    # 2*pi*r*h == 4*pi*r^2 == area of a sphere of radius 20
    nt.eq_(s.radius, 20.0)
    nt.assert_almost_equal(s.area, 5026.548245743669)
    assert_array_equal(s.center, [0, 0, -10])
    nt.ok_('SomaCylinders' in str(s))

    # neuromorpho style
    with warnings.catch_warnings(record=True):
        s = load_neuron(StringIO(u"""
                1 1 0   0 0 10 -1
                2 1 0 -10 0 10  1
                3 1 0  10 0 10  1"""), reader='swc').soma

    nt.ok_('SomaNeuromorphoThreePointCylinders' in str(s))
    nt.eq_(list(s.center), [0., 0., 0.])
    nt.assert_almost_equal(s.area, 1256.6370614)

    # some neuromorpho files don't follow the convention
    #but have (ys + rs) as point 2, and have xs different in each line
    # ex: http://neuromorpho.org/dableFiles/brumberg/CNG%20version/april11s1cell-1.CNG.swc
    with warnings.catch_warnings(record=True):
        s = load_neuron(StringIO(u"""
                1 1  0  0 0 10 -1
                2 1 -2 -6 0 10  1
                3 1  2  6 0 10  1"""), reader='swc').soma

    nt.ok_('SomaNeuromorphoThreePointCylinders' in str(s))
    nt.eq_(list(s.center), [0., 0., 0.])
    nt.assert_almost_equal(s.area, 794.76706126368811, places=4)

    s = load_neuron(StringIO(u"""
                1 1 0  0 0  0 -1
                2 1 0  2 0  2  1
                3 1 0  4 0  4  2
                4 1 0  6 0  6  3
                5 1 0  8 0  8  4
                6 1 0 10 0 10  5"""), reader='swc').soma

    nt.eq_(list(s.center), [0., 0., 0.])
    nt.assert_almost_equal(s.area, 444.288293851) # cone area, not including bottom
