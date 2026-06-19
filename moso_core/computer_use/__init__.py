from moso_core.computer_use.models import (
    AutomationSequence,
    ComputerUseResult,
    KeyboardAction,
    MouseAction,
    RecordedEvent,
    ScreenCapture,
    WindowAction,
)

try:
    from moso_core.computer_use.automation import AutomationEngine
    from moso_core.computer_use.keyboard import KeyboardController
    from moso_core.computer_use.mouse import MouseController
    from moso_core.computer_use.permissions import ComputerUsePermissions
    from moso_core.computer_use.recorder import WorkflowRecorder
    from moso_core.computer_use.screen import ScreenCapturer
    from moso_core.computer_use.windows import WindowManager

    COMPUTER_USE_AVAILABLE = True
except ImportError:
    AutomationEngine = None  # noqa: F811
    KeyboardController = None  # noqa: F811
    MouseController = None  # noqa: F811
    ScreenCapturer = None  # noqa: F811
    WindowManager = None  # noqa: F811
    WorkflowRecorder = None  # noqa: F811
    ComputerUsePermissions = None  # noqa: F811
    COMPUTER_USE_AVAILABLE = False

__all__ = [
    "AutomationEngine",
    "KeyboardController",
    "MouseController",
    "ScreenCapturer",
    "WindowManager",
    "WorkflowRecorder",
    "ComputerUsePermissions",
    "ComputerUseResult",
    "MouseAction",
    "KeyboardAction",
    "ScreenCapture",
    "WindowAction",
    "AutomationSequence",
    "RecordedEvent",
    "COMPUTER_USE_AVAILABLE",
]
