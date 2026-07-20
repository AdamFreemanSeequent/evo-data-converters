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

import os
from typing import Optional
from uuid import uuid4

import pandas as pd
import pyarrow as pa
from evo_schemas.components import (
    BaseSpatialDataProperties_V1_0_1,
    CategoryAttribute_V1_1_0,
    ContinuousAttribute_V1_1_0,
    Crs_V1_0_1,
    NanCategorical_V1_0_1,
    NanContinuous_V1_0_1,
)
from evo_schemas.elements import (
    FloatArray1_V1_0_1,
    FloatArray3_V1_0_1,
    IntegerArray1_V1_0_1,
    LookupTable_V1_0_1,
)
from evo_schemas.objects import Pointset_V1_2_0, Pointset_V1_2_0_Locations
from pandas.api.types import is_numeric_dtype

import evo.logging
from evo.data_converters.common.utils import vertices_bounding_box
from evo.data_converters.adamf.importer.adamf_reader import read_adamf_file
from evo.objects.utils.data import ObjectDataClient

logger = evo.logging.getLogger("data_converters")


def _continuous_attribute(name: str, values: pd.Series, data_client: ObjectDataClient) -> ContinuousAttribute_V1_1_0:
    table = pa.Table.from_arrays([pa.array(values.to_numpy(), type=pa.float64())], names=["data"])
    array = FloatArray1_V1_0_1.from_dict(data_client.save_table(table))
    return ContinuousAttribute_V1_1_0(
        name=name,
        key=str(uuid4()),
        nan_description=NanContinuous_V1_0_1(values=[]),
        values=array,
    )


def _category_attribute(name: str, values: pd.Series, data_client: ObjectDataClient) -> CategoryAttribute_V1_1_0:
    # Build a lookup table mapping each unique value to an integer key, then map the
    # original values onto those keys.
    categories = values.astype("category")
    lookup_table_df = pd.DataFrame(
        {
            "key": range(1, len(categories.cat.categories) + 1),
            "value": categories.cat.categories.astype(str),
        }
    )
    keys = pd.Series(categories.cat.codes + 1, dtype="int64")

    lookup_table = pa.Table.from_arrays(
        [pa.array(lookup_table_df["key"], type=pa.int64()), pa.array(lookup_table_df["value"], type=pa.string())],
        names=["key", "value"],
    )
    values_table = pa.Table.from_arrays([pa.array(keys.to_numpy(), type=pa.int64())], names=["data"])

    table = LookupTable_V1_0_1.from_dict(data_client.save_table(lookup_table))
    mapped_values = IntegerArray1_V1_0_1.from_dict(data_client.save_table(values_table))

    return CategoryAttribute_V1_1_0(
        name=name,
        key=str(uuid4()),
        nan_description=NanCategorical_V1_0_1(values=[]),
        table=table,
        values=mapped_values,
    )


def get_geoscience_object_from_adamf(
    data_client: ObjectDataClient,
    filepath: str,
    coordinate_reference_system: Crs_V1_0_1,
    tags: Optional[dict[str, str]] = None,
) -> BaseSpatialDataProperties_V1_0_1:
    """Build a Pointset Geoscience Object from a ADAMF file.

    :param data_client: Client used to upload referenced data (e.g. attribute arrays via
        ``data_client.save_table``).
    :param filepath: Path to the ADAMF file to convert.
    :param coordinate_reference_system: The CRS to assign to the created Geoscience Object.
    :param tags: (Optional) Additional tags to attach to the Geoscience Object.
    :return: The converted Pointset Geoscience Object.
    """
    # Read the file into an intermediate representation.
    data = read_adamf_file(filepath)

    # Build the standard tags for the object. Extend or override these as needed.
    object_tags = {
        "Source": f"{os.path.basename(filepath)} (via Evo Data Converters)",
        "Stage": "Experimental",
        "InputType": "ADAMF",
    }
    if tags:
        object_tags.update(tags)

    # Save the point coordinates and compute the bounding box.
    bounding_box = vertices_bounding_box(data.points)

    coordinates_table = pa.Table.from_arrays(
        [pa.array(data.points[:, i], type=pa.float64()) for i in range(3)],
        schema=pa.schema([("x", pa.float64()), ("y", pa.float64()), ("z", pa.float64())]),
    )
    coordinates = FloatArray3_V1_0_1.from_dict(data_client.save_table(coordinates_table))

    # Convert every non-coordinate column into a continuous or category attribute.
    attributes: list[ContinuousAttribute_V1_1_0 | CategoryAttribute_V1_1_0] = []
    for name, values in data.attributes.items():
        if is_numeric_dtype(values):
            logger.debug(f'Treating attribute "{name}" as a continuous type.')
            attributes.append(_continuous_attribute(name, values, data_client))
        else:
            logger.debug(f'Treating attribute "{name}" as a category type.')
            attributes.append(_category_attribute(name, values, data_client))

    locations = Pointset_V1_2_0_Locations(coordinates=coordinates, attributes=attributes)

    return Pointset_V1_2_0(
        name=os.path.basename(filepath),
        uuid=None,
        bounding_box=bounding_box,
        coordinate_reference_system=coordinate_reference_system,
        tags=object_tags,
        locations=locations,
    )
