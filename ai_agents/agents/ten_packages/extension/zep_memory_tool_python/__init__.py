#
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file for more information.
#
try:
    from . import addon
except Exception as e:
    import traceback
    traceback.print_exc()
    raise