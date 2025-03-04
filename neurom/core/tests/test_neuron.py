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

from copy import copy, deepcopy
from pathlib import Path

import neurom as nm
import numpy as np
from morphio import Morphology as ImmutMorphology
from morphio.mut import Morphology
from neurom.core import Neuron, graft_neuron, iter_segments
from nose import tools as nt
from numpy.testing import assert_array_equal

SWC_PATH = Path(__file__).parent.parent.parent.parent / 'test_data/swc/'


def test_simple():
    nm.load_neuron(str(SWC_PATH / 'simple.swc'))


def test_load_neuron_pathlib():
    nm.load_neuron(SWC_PATH / 'simple.swc')


def test_load_neuron_from_other_neurons():
    filename = SWC_PATH / 'simple.swc'

    expected_points = [[ 0.,  0.,  0.,  1.],
                       [ 0.,  5.,  0.,  1.],
                       [ 0.,  5.,  0.,  1.],
                       [-5.,  5.,  0.,  0.],
                       [ 0.,  5.,  0.,  1.],
                       [ 6.,  5.,  0.,  0.],
                       [ 0.,  0.,  0.,  1.],
                       [ 0., -4.,  0.,  1.],
                       [ 0., -4.,  0.,  1.],
                       [ 6., -4.,  0.,  0.],
                       [ 0., -4.,  0.,  1.],
                       [-5., -4.,  0.,  0.]]

    assert_array_equal(nm.load_neuron(nm.load_neuron(filename)).points,
                       expected_points)

    assert_array_equal(nm.load_neuron(Morphology(filename)).points,
                       expected_points)

    assert_array_equal(nm.load_neuron(ImmutMorphology(filename)).points,
                       expected_points)


def test_for_morphio():
    Neuron(Morphology())

    neuron = Morphology()
    neuron.soma.points = [[0,0,0], [1,1,1], [2,2,2]]
    neuron.soma.diameters = [1, 1, 1]

    NeuroM_neuron = Neuron(neuron)
    assert_array_equal(NeuroM_neuron.soma.points,
                       [[0., 0., 0., 0.5],
                        [1., 1., 1., 0.5],
                        [2., 2., 2., 0.5]])

    NeuroM_neuron.soma.points = [[1, 1, 1, 1],
                                 [2, 2, 2, 2]]
    assert_array_equal(NeuroM_neuron.soma.points,
                       [[1, 1, 1, 1],
                        [2, 2, 2, 2]])


def _check_cloned_neuron(nrn1, nrn2):
    # check if two neurons are identical

    # soma
    nt.ok_(isinstance(nrn2.soma, type(nrn1.soma)))
    nt.eq_(nrn1.soma.radius, nrn2.soma.radius)

    for v1, v2 in zip(nrn1.soma.iter(), nrn2.soma.iter()):
        nt.ok_(np.allclose(v1, v2))

    # neurites
    for v1, v2 in zip(iter_segments(nrn1), iter_segments(nrn2)):
        (v1_start, v1_end), (v2_start, v2_end) = v1, v2
        nt.ok_(np.allclose(v1_start, v2_start))
        nt.ok_(np.allclose(v1_end, v2_end))

    # check if the ids are different
    # somata
    nt.ok_(nrn1.soma is not nrn2.soma)

    # neurites
    for neu1, neu2 in zip(nrn1.neurites, nrn2.neurites):
        nt.ok_(neu1 is not neu2)

    # check if changes are propagated between neurons
    nrn2.soma.radius = 10.
    nt.ok_(nrn1.soma.radius != nrn2.soma.radius)


def test_copy():
    nrn = nm.load_neuron(SWC_PATH / 'simple.swc')
    _check_cloned_neuron(nrn, copy(nrn))


def test_deepcopy():
    nrn = nm.load_neuron(SWC_PATH / 'simple.swc')
    _check_cloned_neuron(nrn, deepcopy(nrn))


def test_graft_neuron():
    nrn1 = nm.load_neuron(SWC_PATH / 'simple.swc')
    basal_dendrite = nrn1.neurites[0]
    nrn2 = graft_neuron(basal_dendrite.root_node)
    nt.assert_equal(len(nrn2.neurites), 1)
    nt.assert_equal(basal_dendrite, nrn2.neurites[0])


def test_str():
    n = nm.load_neuron(SWC_PATH / 'simple.swc')
    nt.ok_('Neuron' in str(n))
    nt.ok_('Section' in str(n.neurites[0].root_node))
