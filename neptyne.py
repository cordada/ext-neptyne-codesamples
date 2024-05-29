"""This module provides a mock version of the Neptyne API so that editors are happy.

You can find the real Neptyne API at:

"""


import sys
from types import ModuleType

class MockModule(ModuleType):
    def __getattr__(self, name):
        return MockModule(name)

sys.modules[__name__] = MockModule(__name__)