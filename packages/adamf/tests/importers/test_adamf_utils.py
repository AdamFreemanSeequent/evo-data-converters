#  Copyright © 2026 Bentley Systems, Incorporated
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import tempfile
from pathlib import Path

import pytest
from evo_schemas.components import CategoryAttribute_V1_1_0, ContinuousAttribute_V1_1_0
from evo_schemas.objects import Pointset_V1_2_0

from evo.data_converters.common import (
    EvoWorkspaceMetadata,
    create_evo_object_service_and_data_client,
    crs_from_epsg_code,
)
from evo.data_converters.adamf.importer.utils import get_geoscience_object_from_adamf

_SAMPLE_CSV = Path(__file__).parents[2] / "code-samples" / "convert-adamf" / "data" / "input" / "WP_assay.csv"


@pytest.fixture
def data_client():  # type: ignore[no-untyped-def]
    with tempfile.TemporaryDirectory() as cache_root:
        metadata = EvoWorkspaceMetadata(workspace_id="9c86938d-a40f-491a-a3e2-e823ca53c9ae", cache_root=cache_root)
        _, client = create_evo_object_service_and_data_client(metadata)
        yield client


def test_get_geoscience_object_from_adamf_builds_pointset(data_client) -> None:  # type: ignore[no-untyped-def]
    crs = crs_from_epsg_code(32650)

    pointset = get_geoscience_object_from_adamf(data_client, str(_SAMPLE_CSV), crs, tags={"custom": "value"})

    assert isinstance(pointset, Pointset_V1_2_0)
    assert pointset.name == "WP_assay.csv"
    assert pointset.uuid is None
    assert pointset.coordinate_reference_system == crs
    assert pointset.tags["InputType"] == "ADAMF"
    assert pointset.tags["custom"] == "value"

    # Coordinates
    assert pointset.locations.coordinates.length == 8332

    # Attributes: Hole ID is categorical, the rest continuous.
    attributes = pointset.locations.attributes
    assert [attr.name for attr in attributes] == ["Hole ID", "CU_pct", "AU_gpt", "DENSITY"]

    hole_id = attributes[0]
    assert isinstance(hole_id, CategoryAttribute_V1_1_0)
    assert hole_id.values.length == 8332

    for attr in attributes[1:]:
        assert isinstance(attr, ContinuousAttribute_V1_1_0)
        assert attr.values.length == 8332


def test_get_geoscience_object_from_adamf_bounding_box(data_client) -> None:  # type: ignore[no-untyped-def]
    pointset = get_geoscience_object_from_adamf(data_client, str(_SAMPLE_CSV), crs_from_epsg_code(32650))

    bounding_box = pointset.bounding_box
    assert bounding_box.min_x <= bounding_box.max_x
    assert bounding_box.min_y <= bounding_box.max_y
    assert bounding_box.min_z <= bounding_box.max_z
