# Copyright Nicholas Londowski 2022. Apache 2.0 license, see LICENSE file.
import collections
# import requests
import yogger
import unittest


class PFormatTest(unittest.TestCase):
    def test_bytes(self):
        value_to_test = b"this\nis\na\ntest"
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = b'this\\nis\\na\\ntest'"
        self.assertEqual(result_actual, result_expected)

    def test_string(self):
        # Does not contain newlines
        value_to_test = "this is a test"
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = 'this is a test'"
        self.assertEqual(result_actual, result_expected)
        # Contains newlines
        value_to_test = "this\nis\na\ntest"
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = 'this\\nis\\na\\ntest'"
        self.assertEqual(result_actual, result_expected)

    def test_set(self):
        # All values are of type str
        value_to_test = {"this", "is", "a", "test"}
        result_actual = yogger.pformat("value_to_test", value_to_test)
        self.assertRegex(
            result_actual,
            (
                r"^value_to_test = {"
                + r"(?:"
                + r"|".join(
                    [
                        r"'a', 'is', 'test', 'this'",
                        r"'a', 'is', 'this', 'test'",
                        r"'a', 'test', 'is', 'this'",
                        r"'a', 'test', 'this', 'is'",
                        r"'a', 'this', 'is', 'test'",
                        r"'a', 'this', 'test', 'is'",
                        r"'is', 'a', 'test', 'this'",
                        r"'is', 'a', 'this', 'test'",
                        r"'is', 'test', 'a', 'this'",
                        r"'is', 'test', 'this', 'a'",
                        r"'is', 'this', 'a', 'test'",
                        r"'is', 'this', 'test', 'a'",
                        r"'test', 'a', 'is', 'this'",
                        r"'test', 'a', 'this', 'is'",
                        r"'test', 'is', 'a', 'this'",
                        r"'test', 'is', 'this', 'a'",
                        r"'test', 'this', 'a', 'is'",
                        r"'test', 'this', 'is', 'a'",
                        r"'this', 'a', 'is', 'test'",
                        r"'this', 'a', 'test', 'is'",
                        r"'this', 'is', 'a', 'test'",
                        r"'this', 'is', 'test', 'a'",
                        r"'this', 'test', 'a', 'is'",
                        r"'this', 'test', 'is', 'a'",
                    ]
                )
                + r")"
                + r"}$"
            ),
        )
        # All values are of type int
        value_to_test = {0, 1, 2, 3}
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = {0, 1, 2, 3}"
        self.assertEqual(result_actual, result_expected)

    def test_tuple(self):
        # All values are of type str
        value_to_test = ("this", "is", "a", "test")
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = ('this', 'is', 'a', 'test')"
        self.assertEqual(result_actual, result_expected)
        # All values are of type int
        value_to_test = (0, 1, 2, 3)
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = (0, 1, 2, 3)"
        self.assertEqual(result_actual, result_expected)
        # All values are of type str or int
        value_to_test = ("this", 0, "is", 1, "a", 2, "test", 3)
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = ('this', 0, 'is', 1, 'a', 2, 'test', 3)"
        self.assertEqual(result_actual, result_expected)
        # Tuple of tuples whose values are type str
        value_to_test = (("this", "is"), ("a", "test"))
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <builtins.tuple>
  value_to_test[0] = ('this', 'is')
  value_to_test[1] = ('a', 'test')"""
        self.assertEqual(result_actual, result_expected)
        # Tuple of tuples whose values are type int
        value_to_test = ((0, 1), (2, 3))
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <builtins.tuple>
  value_to_test[0] = (0, 1)
  value_to_test[1] = (2, 3)"""
        self.assertEqual(result_actual, result_expected)
        # Tuple of tuples whose values are type str or int
        value_to_test = (("this", 0), ("is", 1), ("a", 2), ("test", 3))
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <builtins.tuple>
  value_to_test[0] = ('this', 0)
  value_to_test[1] = ('is', 1)
  value_to_test[2] = ('a', 2)
  value_to_test[3] = ('test', 3)"""
        self.assertEqual(result_actual, result_expected)

    def test_list(self):
        # All values are of type str
        value_to_test = ["this", "is", "a", "test"]
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = ['this', 'is', 'a', 'test']"
        self.assertEqual(result_actual, result_expected)
        # All values are of type int
        value_to_test = [0, 1, 2, 3]
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = [0, 1, 2, 3]"
        self.assertEqual(result_actual, result_expected)
        # All values are of type str or int
        value_to_test = ["this", 0, "is", 1, "a", 2, "test", 3]
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = ['this', 0, 'is', 1, 'a', 2, 'test', 3]"
        self.assertEqual(result_actual, result_expected)
        # Tuple of lists whose values are type str
        value_to_test = [["this", "is"], ["a", "test"]]
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <builtins.list>
  value_to_test[0] = ['this', 'is']
  value_to_test[1] = ['a', 'test']"""
        self.assertEqual(result_actual, result_expected)
        # Tuple of lists whose values are type int
        value_to_test = [[0, 1], [2, 3]]
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <builtins.list>
  value_to_test[0] = [0, 1]
  value_to_test[1] = [2, 3]"""
        self.assertEqual(result_actual, result_expected)
        # Tuple of lists whose values are type str or int
        value_to_test = [["this", 0], ["is", 1], ["a", 2], ["test", 3]]
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <builtins.list>
  value_to_test[0] = ['this', 0]
  value_to_test[1] = ['is', 1]
  value_to_test[2] = ['a', 2]
  value_to_test[3] = ['test', 3]"""
        self.assertEqual(result_actual, result_expected)

    def test_deque(self):
        # All values are of type str
        value_to_test = collections.deque(["this", "is", "a", "test"])
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = deque(['this', 'is', 'a', 'test'])"
        self.assertEqual(result_actual, result_expected)
        # All values are of type int
        value_to_test = collections.deque([0, 1, 2, 3])
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = deque([0, 1, 2, 3])"
        self.assertEqual(result_actual, result_expected)
        # All values are of type str or int
        value_to_test = collections.deque(["this", 0, "is", 1, "a", 2, "test", 3])
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = "value_to_test = deque(['this', 0, 'is', 1, 'a', 2, 'test', 3])"
        self.assertEqual(result_actual, result_expected)
        # Tuple of deques whose values are type str
        value_to_test = collections.deque([collections.deque(["this", "is"]), collections.deque(["a", "test"])])
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <collections.deque>
  value_to_test[0] = deque(['this', 'is'])
  value_to_test[1] = deque(['a', 'test'])"""
        self.assertEqual(result_actual, result_expected)
        # Tuple of lists whose values are type int
        value_to_test = collections.deque([collections.deque([0, 1]), collections.deque([2, 3])])
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <collections.deque>
  value_to_test[0] = deque([0, 1])
  value_to_test[1] = deque([2, 3])"""
        self.assertEqual(result_actual, result_expected)
        # Tuple of lists whose values are type str or int
        value_to_test = collections.deque(
            [
                collections.deque(["this", 0]),
                collections.deque(["is", 1]),
                collections.deque(["a", 2]),
                collections.deque(["test", 3]),
            ]
        )
        result_actual = yogger.pformat("value_to_test", value_to_test)
        result_expected = """value_to_test = <collections.deque>
  value_to_test[0] = deque(['this', 0])
  value_to_test[1] = deque(['is', 1])
  value_to_test[2] = deque(['a', 2])
  value_to_test[3] = deque(['test', 3])"""
        self.assertEqual(result_actual, result_expected)

    # TODO
    # def test_requests(self):
    #     # NOTE: Request must be successful
    #     # - Must start at the begining of the line
    #     # - Every line after the first is indented with a multiple of 2 spaces
    #     # - Should have no trailing whitespace
    #     r = requests.get("https://api.github.com/events")
    #     # Request that was made
    #     result_actual = yogger.pformat("r.request", r.request)
    #     self.assertRegex(result_actual, r"^r.request = <PreparedRequest \[GET\]>(?:\n(?: {2})+[^\n]+)+$")
    #     # Response from request (includes original request)
    #     result_actual = yogger.pformat("r", r)
    #     self.assertRegex(result_actual, r"^r = <Response \[200\]>(?:\n(?: {2})+[^\n]+)+$")


if __name__ == "__main__":
    unittest.main()
