from functools import reduce
from typing import Any


class RepeatedFlagValueError(Exception):
    pass


def auto(cls):
    if not isinstance(cls, FlaggedEnumMeta):
        raise TypeError
    existing = reduce(lambda acc, fl: acc | fl.value, cls.declared_flags, 0)
    mask = 1
    while mask & existing:
        mask <<= 1
    return mask


class FlaggedEnumMeta(type):
    def __new__(mcs, name, bases, attrs, **kwargs) -> Any:
        return super().__new__(mcs, name, bases, attrs)

    def __init__(cls, name, bases, attrs) -> None:
        cls.__declared_flags = []
        cls.__all_flags = []
        for name, value in attrs.items():
            if cls.__is_flag_definition(name, value):
                new_flag = cls.__make_flag_value(name, value)
                cls.__declared_flags += [new_flag]
                setattr(cls, name, new_flag)
        super().__init__(name, bases, attrs)

    @property
    def declared_flags(self):
        return self.__declared_flags

    @property
    def all_flags(self):
        return self.__all_flags

    def __call__(cls, *args: Any, name, value, **kwargs: Any) -> Any:
        flag = cls.__new__(cls, *args, *kwargs)
        FlaggedEnum.__init__(flag, name=name, value=value)
        cls.__all_flags += [flag]
        return flag

    @staticmethod
    def __is_flag_definition(name, value):
        return (value is auto or not hasattr(value, '__call__')) \
                and not isinstance(value, property) \
                and not name.startswith('_')

    def __make_flag_value(cls, name: str, value) -> Any:
        if value is auto:
            value = auto(cls)
        if not isinstance(value, int):
            raise TypeError
        if any(value & flag.value for flag in cls.__declared_flags):
            raise RepeatedFlagValueError(name)

        return cls(name=name, value=value)

    def __iter__(cls):
        yield from cls.__declared_flags

    def __getitem__(cls, item):
        if isinstance(item, str):
            flag = (fl for fl in cls.__declared_flags if fl.name == item)
        elif isinstance(item, int):
                flag = (fl for fl in cls.__declared_flags if fl.value == item)
        else:
            raise TypeError
        try:
            return next(flag)
        except StopIteration:
            raise IndexError

    def __contains__(cls, item):
        if isinstance(item, cls):
            return item in (fl for fl in cls.__all_flags)
        return False


class FlaggedEnum(int, metaclass=FlaggedEnumMeta):

    def __new__(cls) -> Any:
        return super().__new__(cls)

    def __init__(self, name=None, value=None) -> None:
        self.__name = name
        self.__value = value
        super().__init__()

    @property
    def name(self):
        return self.__name

    @property
    def value(self):
        return self.__value

    def __and__(self, other):
        if type(other) is not type(self):
            raise TypeError
        return self.value & other.value

    def __or__(self, other):
        if type(other) is not type(self):
            raise TypeError

        compound_value = self.value | other.value
        try:
            return FlaggedEnum[compound_value]
        except IndexError:
            compound_name = '{}|{}'.format(self.name, other.name)
            return type(self)(name=compound_name, value=compound_value)

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        cls = type(self)
        if self in cls.declared_flags:
            return '{}.{}({})'.format(cls.__name__, self.name, self.value)
        else:
            return ' | '.join(str(fl) for fl in cls.declared_flags if self & fl)
