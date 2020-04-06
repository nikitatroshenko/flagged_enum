import functools
import itertools
import unittest

from flag import FlaggedEnum, auto, RepeatedFlagValueError, IllegalFlagValueError


class MyAutoEnum(FlaggedEnum):
    read_only = auto
    lowercase = 1
    immediate = auto


class MyEnum(FlaggedEnum):
    read_only = (1 << 0)
    lowercase = (1 << 1)
    immediate = (1 << 2)


class FlaggedEnumTest(unittest.TestCase):

    def test_explicit_create(self):
        self.assertEqual(MyEnum.read_only.value, 1 << 0)
        self.assertEqual(MyEnum.read_only.name, 'read_only')
        self.assertEqual(MyEnum.lowercase.value, 1 << 1)
        self.assertEqual(MyEnum.lowercase.name, 'lowercase')
        self.assertEqual(MyEnum.immediate.value, 1 << 2)
        self.assertEqual(MyEnum.immediate.name, 'immediate')

    def test_auto_create(self):
        self.assertEqual(MyAutoEnum.read_only.name, 'read_only')
        self.assertEqual(MyAutoEnum.lowercase.name, 'lowercase')
        self.assertEqual(MyAutoEnum.immediate.name, 'immediate')
        for f1, f2 in itertools.combinations(MyAutoEnum, 2):
            self.assertFalse(f1.value & f2.value)

    def test_clashing_create(self):
        with self.assertRaises(RepeatedFlagValueError):
            class MyClashingFlagsEnum(FlaggedEnum):
                read_only = 1
                lowercase = 1
        with self.assertRaises(IllegalFlagValueError):
            class MyIllegalFlagsEnum(FlaggedEnum):
                read_only = 1
                lowercase = 'lowercase'

    def test_or_and(self):
        lowercase_readonly = MyAutoEnum.lowercase | MyAutoEnum.read_only
        another_lowercase_readonly = MyAutoEnum.lowercase | MyAutoEnum.read_only
        self.assertEqual(lowercase_readonly, another_lowercase_readonly)
        self.assertTrue(lowercase_readonly.value & MyAutoEnum.read_only.value)
        self.assertTrue(lowercase_readonly & MyAutoEnum.read_only)
        self.assertTrue(lowercase_readonly.value & MyAutoEnum.lowercase.value)
        self.assertTrue(lowercase_readonly & MyAutoEnum.lowercase)

    def test_iter(self):
        omniflag = functools.reduce(lambda fl1, fl2: fl1 | fl2, MyAutoEnum)
        for flag in MyAutoEnum:
            self.assertTrue(omniflag & flag)

    def test_instance(self):
        for flag in MyAutoEnum:
            self.assertIsInstance(flag, int)
            self.assertIsInstance(flag, MyAutoEnum)
        for flag1, flag2 in itertools.combinations(MyAutoEnum, 2):
            self.assertIsInstance(flag1 | flag2, MyAutoEnum)
            self.assertIsInstance(flag1 | flag2, int)

    def test_getitem(self):
        read_only_by_val = MyEnum[1 << 0]
        read_only_by_name = MyEnum['read_only']
        self.assertIs(read_only_by_val, MyEnum.read_only)
        self.assertIs(read_only_by_name, MyEnum.read_only)

        with self.assertRaises(IndexError):
            nonexistent = MyEnum['nonexistent']
        with self.assertRaises(IndexError):
            nonexistent = MyEnum[322]

    def test_contains(self):
        for flag in MyEnum:
            self.assertIn(flag, MyEnum)
        for flag1, flag2 in itertools.combinations(MyEnum, 2):
            self.assertIn(flag1 | flag2, MyEnum)


if __name__ == '__main__':
    unittest.main()
