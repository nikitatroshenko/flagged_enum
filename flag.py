from functools import reduce
from types import FunctionType
from typing import Any, Dict, Tuple, Union


class RepeatedFlagValueError(Exception):
    pass


class IllegalFlagValueError(Exception):
    pass


class AutoGen:
    """
    Generates legal flag values for enums
    """

    def __init__(self, *reserved_values: Tuple[int, ...]) -> None:
        """
        Creates new flag value generator
        :param reserved_values: values to be skipped during flags generation
        """
        self._reserved_values = reduce(lambda acc, val: acc | val, reserved_values, 0)
        super().__init__()

    def __next__(self) -> int:
        """
        Retrieves next legal flag value
        :return: next legal flag value
        """
        next_val = ~self._reserved_values - (~self._reserved_values & (~self._reserved_values - 1))
        self._reserved_values |= next_val
        return next_val


auto = AutoGen


class FlaggedEnumMeta(type):
    """
    Meta class for all flagged enums. Allows declaring class attributes
    as unique flags, also allows automatic flag values generation via
    AutoGen flag value suppliers
    Provides ability to test flags types, iterate by declared flags and
    get flags by their names/values
    """

    def __new__(mcs: type, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any], auto_gen_cls=auto) -> Any:
        return super().__new__(mcs, name, bases, attrs)

    def __init__(cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any], auto_gen_cls=auto) -> None:
        cls.name = property(lambda self: self._name)
        cls.value = property(lambda self: self._value)

        cls._all_flags = set()
        declared_flags = {cls(name=attr_name, value=attr_value)
                          for attr_name, attr_value
                          in attrs.items()
                          if cls._is_flag_def(attr_name, attr_value)
                          and attr_value is not auto_gen_cls}

        auto_gen = auto_gen_cls(*(flag.value for flag in declared_flags))
        for attr_name, attr_value in attrs.items():
            if attr_value is auto_gen_cls:
                declared_flags.add(cls(name=attr_name, value=next(auto_gen)))

        cls._declared_flags = frozenset(declared_flags)
        cls._assert_unique_flags()
        for flag in cls._declared_flags:
            setattr(cls, flag.name, flag)

        super().__init__(name, bases, attrs)

    def __call__(cls, *args: Any, name: str, value: Any, **kwargs: Any) -> Any:
        if not isinstance(value, int):
            raise IllegalFlagValueError(f'{value} is not legal flag value')
        flag = super().__call__(*args, **kwargs)
        flag._name = name
        flag._value = value
        cls._all_flags.add(flag)
        return flag

    @staticmethod
    def _is_flag_def(name: str, value: Any) -> bool:
        return not isinstance(value, (FunctionType, property, classmethod, staticmethod)) \
               and not name.startswith('_')

    def _assert_unique_flags(cls):
        composition = 0
        for flag in cls._declared_flags:
            if composition & flag.value:
                raise RepeatedFlagValueError(flag.name)
            composition |= flag.value

    def __iter__(cls):
        yield from cls._declared_flags

    def get_by_name(cls, name: str):
        try:
            return getattr(cls, name)
        except AttributeError:
            raise IndexError(f'No declared flag with name {name}')

    def get_by_value(cls, value: int):
        for flag in cls._declared_flags:
            if flag.value == value:
                return flag
        else:
            raise IndexError(f'No declared flag with value ({value})')

    def __getitem__(cls, item: Union[int, str]):
        if isinstance(item, str):
            return cls.get_by_name(item)
        elif isinstance(item, int):
            return cls.get_by_value(item)

    def __contains__(cls, item):
        return isinstance(item, cls) and item in cls._all_flags


class FlaggedEnum(int, metaclass=FlaggedEnumMeta):
    """
    Base class for flagged enums. Supplies flag check and combination methods
    """

    def __and__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError
        return self.value & other.value

    def __or__(self, other):
        cls = self.__class__
        if not isinstance(other, cls):
            raise TypeError

        compound_value = self.value | other.value
        for flag in cls._all_flags:
            if flag.value == compound_value:
                return flag
        else:
            compound_name = f'{self.name}|{other.name}'
            return cls(name=compound_name, value=compound_value)

    def __hash__(self):
        return self.value

    def __eq__(self, other):
        return self is other

    def __str__(self):
        cls = self.__class__
        if self in cls:
            return f'{cls.__name__}.{self.name}({self.value})'
        else:
            return ' | '.join(str(flag) for flag in cls if self & flag)
