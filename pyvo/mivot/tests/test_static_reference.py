"""
Created on Feb 26, 2021

@author: laurentmichel
"""
import os
import pytest
from pyvo.mivot.utils.xml_utils import XmlUtils
from pyvo.mivot.seekers.annotation_seeker import AnnotationSeeker
from pyvo.mivot.features.static_reference_resolver import StaticReferenceResolver
from pyvo.utils import activate_features
activate_features('MIVOT')


@pytest.fixture
def a_seeker(data_path):
    mapping_block = XmlUtils.xmltree_from_file(
        os.path.join(data_path, "data/input/test.0.xml"))
    return AnnotationSeeker(mapping_block.getroot())


@pytest.fixture
def instance(data_path):
    return XmlUtils.xmltree_from_file(os.path.join(data_path, "data/input/test.4.xml"))


def test_static_reference_resolve(a_seeker, instance, data_path):
    StaticReferenceResolver.resolve(a_seeker, None, instance)
    XmlUtils.assertXmltreeEqualsFile(instance,
                                     os.path.join(data_path, "data/output/test.4.1.xml"))


@pytest.fixture
def data_path():
    return os.path.dirname(os.path.realpath(__file__))


if __name__ == '__main__':
    pytest.main()
