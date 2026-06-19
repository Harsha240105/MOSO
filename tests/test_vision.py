from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from moso_core.vision.models import BoundingBox, OCRResult, ScreenContext, WindowInfo


class FakeIdentityAllowed:
    def get_identity_level(self):
        return "owner"

    def is_owner(self):
        return True


class FakeIdentityDenied:
    def get_identity_level(self):
        return "guest"

    def is_owner(self):
        return False


class TestModels:
    def test_bounding_box_defaults(self):
        bb = BoundingBox(left=10, top=20, width=100, height=50)
        d = bb.to_dict()
        assert d["left"] == 10
        assert d["top"] == 20
        assert d["width"] == 100
        assert d["height"] == 50

    def test_ocr_result_to_dict(self):
        bb = BoundingBox(left=0, top=0, width=50, height=20)
        ocr = OCRResult(text="hello", confidence=0.95, bounding_box=bb)
        d = ocr.to_dict()
        assert d["text"] == "hello"
        assert d["confidence"] == 0.95
        assert "bounding_box" in d

    def test_window_info_defaults(self):
        wi = WindowInfo(title="Chrome")
        assert wi.active is False
        assert wi.bounds is None

    def test_window_info_active(self):
        wi = WindowInfo(title="Chrome", active=True, bounds=(0, 0, 1920, 1080))
        d = wi.to_dict()
        assert d["title"] == "Chrome"
        assert d["active"] is True

    def test_screen_context_defaults(self):
        ctx = ScreenContext()
        assert ctx.timestamp != ""
        assert ctx.resolution == (0, 0)
        assert ctx.windows == []
        assert ctx.ocr_results == []

    def test_screen_context_to_dict(self):
        ctx = ScreenContext(
            resolution=(1920, 1080),
            active_window="Chrome",
            windows=["Chrome", "Terminal"],
            text_content="Hello World",
        )
        d = ctx.to_dict()
        assert d["resolution"] == [1920, 1080]
        assert d["active_window"] == "Chrome"
        assert len(d["windows"]) == 2

    def test_screen_context_summary(self):
        ctx = ScreenContext(
            resolution=(1920, 1080),
            active_window="Chrome",
            windows=["Chrome", "VS Code"],
            text_content="Hello World",
        )
        s = ctx.summary()
        assert "Active Window: Chrome" in s
        assert "Open Windows" in s
        assert "Visible Text:" in s
        assert "1920x1080" in s

    def test_screen_context_summary_empty(self):
        ctx = ScreenContext()
        s = ctx.summary()
        assert "Active Window:" in s


class TestOCR:
    def test_extract_text_returns_string(self):
        from moso_core.vision.ocr import extract_text
        with patch("moso_core.vision.ocr._pytesseract.image_to_string", return_value="hello world\n"):
            result = extract_text(MagicMock())
            assert result == "hello world"

    def test_extract_text_empty(self):
        from moso_core.vision.ocr import extract_text
        with patch("moso_core.vision.ocr._pytesseract.image_to_string", return_value=""):
            result = extract_text(MagicMock())
            assert result == ""

    def test_extract_text_import_error(self):
        import importlib
        import moso_core.vision.ocr as ocr_module
        ocr_module._OCR_AVAILABLE = False
        ocr_module._pytesseract = None
        result = ocr_module.extract_text(MagicMock())
        assert result == ""
        ocr_module._OCR_AVAILABLE = True
        importlib.reload(ocr_module)

    def test_extract_text_regions_returns_list(self):
        from moso_core.vision.ocr import extract_text_regions
        with patch("moso_core.vision.ocr._pytesseract.image_to_data") as mock_ts:
            mock_ts.return_value = {
                "text": ["hello", "", "world"],
                "conf": ["95", "-1", "87"],
                "left": [10, 0, 100],
                "top": [20, 0, 200],
                "width": [50, 0, 60],
                "height": [20, 0, 25],
            }
            results = extract_text_regions(MagicMock())
            assert len(results) == 2
            assert results[0].text == "hello"
            assert results[0].confidence == 95.0
            assert results[1].text == "world"
            assert results[1].confidence == 87.0

    def test_extract_text_regions_empty(self):
        from moso_core.vision.ocr import extract_text_regions
        with patch("moso_core.vision.ocr._pytesseract.image_to_data") as mock_ts:
            mock_ts.return_value = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
            results = extract_text_regions(MagicMock())
            assert results == []

    def test_extract_text_regions_filters_small_regions(self):
        from moso_core.vision.ocr import extract_text_regions
        with patch("moso_core.vision.ocr._pytesseract.image_to_data") as mock_ts:
            mock_ts.return_value = {
                "text": ["tiny", "big"],
                "conf": ["90", "85"],
                "left": [0, 10],
                "top": [0, 20],
                "width": [1, 100],
                "height": [1, 50],
            }
            results = extract_text_regions(MagicMock())
            assert len(results) == 1
            assert results[0].text == "big"


class TestScreenshotAnalysis:
    def test_analyze_screenshot_no_capturer(self):
        from moso_core.vision.screenshot_analysis import analyze_screenshot
        result = analyze_screenshot(screen_capturer=None)
        assert "text" in result

    def test_analyze_screenshot_capture_fails(self):
        from moso_core.vision.screenshot_analysis import analyze_screenshot
        mock_capturer = MagicMock()
        mock_capturer.capture_screen.return_value = MagicMock(success=False, error="fail")
        result = analyze_screenshot(screen_capturer=mock_capturer)
        assert "error" in result
        assert result["text"] == ""

    def test_analyze_screenshot_success(self):
        from moso_core.vision.screenshot_analysis import analyze_screenshot
        mock_capturer = MagicMock()
        mock_capturer.capture_screen.return_value = MagicMock(
            success=True,
            result={"image_path": "/fake/path.png", "resolution": (1920, 1080)},
        )
        with patch("moso_core.vision.screenshot_analysis.extract_text", return_value="hello"):
            with patch("moso_core.vision.screenshot_analysis.extract_text_regions", return_value=[]):
                with patch("PIL.Image.open"):
                    with patch("moso_core.computer_use.windows.WindowManager") as mock_wm:
                        mock_wm_instance = MagicMock()
                        mock_wm_instance.list_windows.return_value = MagicMock(
                            success=True, result={"windows": ["Chrome"]}
                        )
                        mock_wm_instance.get_active_window.return_value = MagicMock(
                            success=True, result={"title": "Chrome"}
                        )
                        mock_wm.return_value = mock_wm_instance
                        result = analyze_screenshot(screen_capturer=mock_capturer)
                        assert result["text"] == "hello"
                        assert "Chrome" in result["windows"]
                        assert result["active_window"] == "Chrome"


class TestContext:
    def test_build_context_no_capturer(self):
        from moso_core.vision.context import build_context
        ctx = build_context(screen_capturer=None)
        assert isinstance(ctx, ScreenContext)

    def test_build_context_success(self):
        from moso_core.vision.context import build_context
        mock_capturer = MagicMock()
        mock_capturer.capture_screen.return_value = MagicMock(
            success=True,
            result={"image_path": "/fake/path.png", "resolution": (1920, 1080)},
        )
        with patch("moso_core.vision.context.extract_text", return_value="screen text"):
            with patch("moso_core.vision.context.extract_text_regions", return_value=[]):
                with patch("PIL.Image.open"):
                    with patch("moso_core.computer_use.windows.WindowManager") as mock_wm:
                        mock_wm_instance = MagicMock()
                        mock_wm_instance.list_windows.return_value = MagicMock(
                            success=True, result={"windows": ["Chrome", "Terminal"]}
                        )
                        mock_wm_instance.get_active_window.return_value = MagicMock(
                            success=True, result={"title": "Chrome"}
                        )
                        mock_wm.return_value = mock_wm_instance
                        ctx = build_context(screen_capturer=mock_capturer)
                        assert ctx.text_content == "screen text"
                        assert ctx.active_window == "Chrome"
                        assert len(ctx.windows) == 2
                        assert ctx.resolution == (1920, 1080)


class TestVisionManager:
    def test_get_screen_text_denied_for_guest(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityDenied())
        text = mgr.get_screen_text()
        assert text == ""

    def test_get_screen_text_allowed_for_owner(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityAllowed())
        with patch("moso_core.vision.manager.build_context") as mock_build:
            mock_ctx = MagicMock()
            mock_ctx.text_content = "visible text"
            mock_build.return_value = mock_ctx
            text = mgr.get_screen_text()
            assert text == "visible text"

    def test_get_active_window_denied(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityDenied())
        title = mgr.get_active_window()
        assert title == ""

    def test_get_active_window_allowed(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityAllowed())
        with patch("moso_core.computer_use.windows.WindowManager") as mock_wm:
            mock_wm_instance = MagicMock()
            mock_wm_instance.get_active_window.return_value = MagicMock(
                success=True, result={"title": "Chrome"}
            )
            mock_wm.return_value = mock_wm_instance
            title = mgr.get_active_window()
            assert title == "Chrome"

    def test_build_context_denied(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityDenied())
        ctx = mgr.build_context()
        assert ctx.text_content == ""
        assert ctx.ocr_results == []

    def test_build_context_allowed(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityAllowed())
        with patch("moso_core.vision.manager.build_context") as mock_build:
            mock_ctx = MagicMock()
            mock_ctx.text_content = "text"
            mock_ctx.ocr_results = []
            mock_build.return_value = mock_ctx
            ctx = mgr.build_context()
            assert ctx.text_content == "text"

    def test_capture_and_analyze_denied(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityDenied())
        result = mgr.capture_and_analyze()
        assert "error" in result

    def test_capture_and_analyze_allowed(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=FakeIdentityAllowed())
        with patch("moso_core.vision.manager.build_context") as mock_build:
            mock_ctx = MagicMock()
            mock_ctx.text_content = "text"
            mock_ctx.ocr_results = []
            mock_ctx.active_window = "Chrome"
            mock_ctx.windows = ["Chrome"]
            mock_ctx.resolution = (1920, 1080)
            mock_ctx.to_dict.return_value = {
                "text_content": "text", "ocr_results": [],
                "active_window": "Chrome", "windows": ["Chrome"],
                "resolution": [1920, 1080], "timestamp": "now",
            }
            mock_ctx.summary.return_value = "summary"
            mock_build.return_value = mock_ctx
            result = mgr.capture_and_analyze()
            assert "text_content" in result

    def test_resource_check_skips_ocr(self):
        from moso_core.vision.manager import VisionManager
        mock_resources = MagicMock()
        mock_status = MagicMock()
        mock_cpu = MagicMock()
        mock_cpu.percent = 95
        mock_status.cpu = mock_cpu
        mock_ram = MagicMock()
        mock_ram.percent = 95
        mock_status.ram = mock_ram
        mock_resources.get_system_status.return_value = mock_status
        mgr = VisionManager(identity=FakeIdentityAllowed(), resources=mock_resources)
        with patch("moso_core.vision.manager.build_context") as mock_build:
            mock_ctx = MagicMock()
            mock_ctx.text_content = "text"
            mock_ctx.ocr_results = [MagicMock()]
            mock_ctx.active_window = "Chrome"
            mock_ctx.windows = ["Chrome"]
            mock_ctx.resolution = (1920, 1080)
            mock_build.return_value = mock_ctx
            ctx = mgr.build_context()
            assert ctx.text_content == ""

    def test_memory_logging_on_capture(self):
        from moso_core.vision.manager import VisionManager
        mock_memory = MagicMock()
        mgr = VisionManager(identity=FakeIdentityAllowed(), memory=mock_memory)
        with patch("moso_core.vision.manager.build_context") as mock_build:
            mock_ctx = MagicMock()
            mock_ctx.text_content = "text"
            mock_ctx.ocr_results = []
            mock_ctx.active_window = "Chrome"
            mock_ctx.windows = ["Chrome"]
            mock_ctx.resolution = (1920, 1080)
            mock_ctx.to_dict.return_value = {
                "text_content": "text", "ocr_results": [],
                "active_window": "Chrome", "windows": ["Chrome"],
                "resolution": [1920, 1080], "timestamp": "now",
            }
            mock_ctx.summary.return_value = "summary"
            mock_build.return_value = mock_ctx
            mgr.capture_and_analyze()
            mock_memory.store_event.assert_called_once()

    def test_no_identity_allows_access(self):
        from moso_core.vision.manager import VisionManager
        mgr = VisionManager(identity=None)
        with patch("moso_core.vision.manager.build_context") as mock_build:
            mock_ctx = MagicMock()
            mock_ctx.text_content = "text"
            mock_ctx.ocr_results = []
            mock_build.return_value = mock_ctx
            text = mgr.get_screen_text()
            assert text == "text"
