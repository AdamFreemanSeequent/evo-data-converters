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

from collections import OrderedDict
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

#: Names of the columns that hold point coordinates. All remaining columns are treated as attributes.
COORDINATE_COLUMNS = ("X", "Y", "Z")


class ADAMFInvalidDataError(Exception):
    """Raised when the contents of a ADAMF file are malformed or fail validation."""


class ADAMFDataFileIOError(Exception):
    """Raised when a ADAMF file cannot be opened or read."""


@dataclass
class ADAMFData:
    """Intermediate representation of a ADAMF file.

    :param points: Array of point coordinates with shape ``(N, 3)`` holding the X, Y and Z values.
    :param attributes: Mapping of attribute name to the pandas Series of values for that column,
        preserving the column order from the file. Every non-coordinate column becomes an attribute.
    """

    points: npt.NDArray[np.float64]
    attributes: "OrderedDict[str, pd.Series]"


def read_adamf_file(filepath: str) -> ADAMFData:
    """Read a ADAMF file from disk into an intermediate representation.

    A ADAMF file is a CSV file that must contain ``X``, ``Y`` and ``Z`` coordinate columns.
    Any additional columns are read as point attributes.

    :param filepath: Path to the ADAMF file to read.
    :return: An :class:`ADAMFData` instance holding the point coordinates and attribute columns.

    :raise ADAMFDataFileIOError: If the file cannot be opened or read.
    :raise ADAMFInvalidDataError: If the file contents are invalid.
    """
    try:
        input_df = pd.read_csv(filepath)
    except FileNotFoundError as exc:
        raise ADAMFDataFileIOError(f"Could not open ADAMF file: {filepath}") from exc
    except pd.errors.EmptyDataError as exc:
        raise ADAMFInvalidDataError(f"ADAMF file is empty: {filepath}") from exc
    except (OSError, pd.errors.ParserError) as exc:
        raise ADAMFDataFileIOError(f"Could not read ADAMF file: {filepath}") from exc

    missing_columns = [column for column in COORDINATE_COLUMNS if column not in input_df.columns]
    if missing_columns:
        raise ADAMFInvalidDataError(
            f"ADAMF file is missing required coordinate column(s): {', '.join(missing_columns)}"
        )

    if input_df.empty:
        raise ADAMFInvalidDataError(f"ADAMF file contains no data rows: {filepath}")

    coordinates_df = input_df[list(COORDINATE_COLUMNS)]
    if coordinates_df.isnull().to_numpy().any():
        raise ADAMFInvalidDataError("ADAMF file contains missing X, Y or Z coordinate values.")

    points = coordinates_df.to_numpy(dtype=np.float64)

    attributes: "OrderedDict[str, pd.Series]" = OrderedDict()
    for column in input_df.columns:
        if column in COORDINATE_COLUMNS:
            continue
        attributes[str(column)] = input_df[column]

    return ADAMFData(points=points, attributes=attributes)
