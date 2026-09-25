from pathlib import Path
from typing import Any
from file_manager import FilePaths, load_pickle_dict
import numpy.typing as npt
import numpy as np

type d_vec_type = dict[str, npt.NDArray[np.float64]]

class DVectorManager:
    _raw_data: dict[str, Any]
        
    def __init__(self, path: Path = FilePaths.HERO_D_VECTORS.value):
        self._raw_data = load_pickle_dict(path)

    @property
    def vec(self) -> d_vec_type:
        """Should be the same as buff vectors"""
        return self._raw_data['desire_vectors']

    @property
    def debuff(self) -> npt.NDArray[np.float64]:
        return self._raw_data['debuff_vector']
        