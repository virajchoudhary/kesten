from dataclasses import dataclass
from typing import Any


def _immutable(*args, **kwargs):
    raise TypeError("Dataset payload is immutable.")


class _FrozenDict(dict):
    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable

    def __deepcopy__(self, memo):
        return self


class _FrozenList(list):
    __setitem__ = _immutable
    __delitem__ = _immutable
    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable

    def __deepcopy__(self, memo):
        return self


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        frozen = _FrozenDict()
        for key, item in value.items():
            dict.__setitem__(frozen, key, _freeze(item))
        return frozen
    if isinstance(value, list):
        frozen = _FrozenList()
        for item in value:
            list.append(frozen, _freeze(item))
        return frozen
    return value


@dataclass(frozen=True, slots=True)
class Dataset:
    payload: dict[str, Any]
    version: str
    instrument_id: str
    data_kind: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze(self.payload))
