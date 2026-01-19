#
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file for more information.
#
try:
    from ten_runtime import (
        Addon,
        register_addon_as_extension,
        TenEnv,
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    from .extension import MemoToolExtension
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

try:
    @register_addon_as_extension("memo_tool_python")
    class MemoToolExtensionAddon(Addon):

        def on_create_instance(self, ten_env: TenEnv, name: str, context) -> None:
            ten_env.log_info(f"[MemoToolAddon] on_create_instance called with name: {name}")
            try:
                ten_env.log_info("[MemoToolAddon] on_create_instance: importing MemoToolExtension...")
                from .extension import MemoToolExtension
                ten_env.log_info("[MemoToolAddon] on_create_instance: MemoToolExtension imported successfully")

                ten_env.log_info(f"[MemoToolAddon] on_create_instance: creating MemoToolExtension instance...")
                extension_instance = MemoToolExtension(name)
                ten_env.log_info(f"[MemoToolAddon] on_create_instance: MemoToolExtension instance created successfully")

                ten_env.log_info("[MemoToolAddon] on_create_instance: calling on_create_instance_done...")
                ten_env.on_create_instance_done(extension_instance, context)
                ten_env.log_info("[MemoToolAddon] on_create_instance: completed successfully")
            except Exception as e:
                error_msg = f"[MemoToolAddon] on_create_instance ERROR: {e}"
                ten_env.log_error(error_msg)
                import traceback
                ten_env.log_error(traceback.format_exc())
                raise
except Exception as e:
    import traceback
    traceback.print_exc()
    raise
