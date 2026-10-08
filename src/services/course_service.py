"""Compatibility alias; implementation lives in MVC controllers."""

import sys
from src.controllers import course_operations_controller as _implementation

sys.modules[__name__] = _implementation
