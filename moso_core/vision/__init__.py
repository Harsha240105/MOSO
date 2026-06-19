from moso_core.vision.models import BoundingBox, OCRResult, ScreenContext, WindowInfo

try:
    from moso_core.vision.ocr import extract_text, extract_text_regions
    from moso_core.vision.screenshot_analysis import analyze_screenshot
    from moso_core.vision.context import build_context
    from moso_core.vision.manager import VisionManager

    VISION_AVAILABLE = True
except ImportError:
    extract_text = None  # noqa: F811
    extract_text_regions = None  # noqa: F811
    analyze_screenshot = None  # noqa: F811
    build_context = None  # noqa: F811
    VisionManager = None  # noqa: F811
    VISION_AVAILABLE = False

__all__ = [
    "BoundingBox",
    "OCRResult",
    "ScreenContext",
    "WindowInfo",
    "extract_text",
    "extract_text_regions",
    "analyze_screenshot",
    "build_context",
    "VisionManager",
    "VISION_AVAILABLE",
]
