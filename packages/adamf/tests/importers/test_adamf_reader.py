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

from pathlib import Path

import numpy as np
import pytest

from evo.data_converters.adamf.importer.adamf_reader import (
    ADAMFData,
    ADAMFDataFileIOError,
    ADAMFInvalidDataError,
    read_adamf_file,
)

_SAMPLE_CSV = Path(__file__).parents[2] / "code-samples" / "convert-adamf" / "data" / "input" / "WP_assay.csv"


def _write_csv(tmp_path: Path, contents: str) -> str:
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(contents)
    return str(csv_path)


def test_read_adamf_file_parses_sample_csv() -> None:
    data = read_adamf_file(str(_SAMPLE_CSV))

    assert isinstance(data, ADAMFData)
    assert data.points.shape == (8332, 3)
    assert data.points.dtype == np.float64
    assert list(data.attributes.keys()) == ["Hole ID", "CU_pct", "AU_gpt", "DENSITY"]


def test_read_adamf_file_parses_coordinates_and_attributes(tmp_path: Path) -> None:
    csv_path = _write_csv(
        tmp_path,
        "X,Y,Z,Hole ID,CU_pct\n1.0,2.0,3.0,WP001,0.5\n4.0,5.0,6.0,WP002,0.6\n",
    )

    data = read_adamf_file(csv_path)

    np.testing.assert_array_equal(data.points, np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))
    assert list(data.attributes.keys()) == ["Hole ID", "CU_pct"]
    assert list(data.attributes["Hole ID"]) == ["WP001", "WP002"]
    assert list(data.attributes["CU_pct"]) == [0.5, 0.6]


def test_read_adamf_file_missing_file_raises_io_error() -> None:
    with pytest.raises(ADAMFDataFileIOError):
        read_adamf_file("does_not_exist.csv")


def test_read_adamf_file_missing_coordinate_column_raises_invalid_data_error(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "X,Y,Attr\n1.0,2.0,foo\n")

    with pytest.raises(ADAMFInvalidDataError, match="Z"):
        read_adamf_file(csv_path)


def test_read_adamf_file_empty_file_raises_invalid_data_error(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "")

    with pytest.raises(ADAMFInvalidDataError):
        read_adamf_file(csv_path)


def test_read_adamf_file_no_data_rows_raises_invalid_data_error(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "X,Y,Z,Attr\n")

    with pytest.raises(ADAMFInvalidDataError):
        read_adamf_file(csv_path)


def test_read_adamf_file_missing_coordinate_value_raises_invalid_data_error(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "X,Y,Z\n1.0,2.0,3.0\n4.0,,6.0\n")

    with pytest.raises(ADAMFInvalidDataError):
        read_adamf_file(csv_path)
