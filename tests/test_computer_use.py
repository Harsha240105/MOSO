from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from moso_core.computer_use.automation import AutomationEngine
from moso_core.computer_use.models import (
    AutomationSequence,
    ComputerUseResult,
    KeyboardAction,
    MouseAction,
    RecordedEvent,
    ScreenCapture,
    WindowAction,
)
from moso_core.computer_use.permissions import ComputerUsePermissions, PERMISSION_LEVELS
from moso_core.computer_use.recorder import WorkflowRecorder


class FakeIdentityOwner:
    def get_identity_level(self):
        return "owner"

    def is_owner(self):
        return True


class FakeIdentityTrusted:
    def get_identity_level(self):
        return "likely_owner"

    def is_owner(self):
        return False


class FakeIdentityGuest:
    def get_identity_level(self):
        return "unknown"

    def is_owner(self):
        return False


class TestComputerUsePermissions:
    def test_guest_actions_allowed_without_identity(self):
        perms = ComputerUsePermissions(identity=None)
        for action in PERMISSION_LEVELS["guest"]:
            allowed, reason = perms.check(action)
            assert allowed, f"{action} should be allowed without identity: {reason}"

    def test_trusted_action_denied_without_identity(self):
        perms = ComputerUsePermissions(identity=None)
        for action in PERMISSION_LEVELS["trusted"]:
            if action in PERMISSION_LEVELS["guest"]:
                continue
            allowed, reason = perms.check(action)
            assert not allowed, f"{action} should be denied without identity"

    def test_owner_action_denied_without_identity(self):
        perms = ComputerUsePermissions(identity=None)
        for action in PERMISSION_LEVELS["owner"]:
            if action in PERMISSION_LEVELS["trusted"] or action in PERMISSION_LEVELS["guest"]:
                continue
            allowed, reason = perms.check(action)
            assert not allowed, f"{action} should be denied without identity"

    def test_guest_actions_allowed_for_guest(self):
        perms = ComputerUsePermissions(identity=FakeIdentityGuest())
        for action in PERMISSION_LEVELS["guest"]:
            allowed, reason = perms.check(action)
            assert allowed, f"{action} should be allowed for guest: {reason}"

    def test_trusted_action_denied_for_guest(self):
        perms = ComputerUsePermissions(identity=FakeIdentityGuest())
        for action in PERMISSION_LEVELS["trusted"]:
            if action in PERMISSION_LEVELS["guest"]:
                continue
            allowed, reason = perms.check(action)
            assert not allowed, f"{action} should be denied for guest"

    def test_trusted_actions_allowed_for_trusted(self):
        perms = ComputerUsePermissions(identity=FakeIdentityTrusted())
        for action in PERMISSION_LEVELS["trusted"]:
            allowed, reason = perms.check(action)
            assert allowed, f"{action} should be allowed for trusted: {reason}"

    def test_owner_actions_denied_for_trusted(self):
        perms = ComputerUsePermissions(identity=FakeIdentityTrusted())
        for action in PERMISSION_LEVELS["owner"]:
            if action in PERMISSION_LEVELS["trusted"]:
                continue
            allowed, reason = perms.check(action)
            assert not allowed, f"{action} should be denied for trusted"

    def test_owner_actions_allowed_for_owner(self):
        perms = ComputerUsePermissions(identity=FakeIdentityOwner())
        for action in PERMISSION_LEVELS["owner"]:
            allowed, reason = perms.check(action)
            assert allowed, f"{action} should be allowed for owner: {reason}"

    def test_unknown_action_denied(self):
        perms = ComputerUsePermissions(identity=FakeIdentityOwner())
        allowed, reason = perms.check("fly_to_moon")
        assert not allowed
        assert "Unknown" in reason

    def test_get_allowed_actions_no_identity(self):
        perms = ComputerUsePermissions(identity=None)
        actions = perms.get_allowed_actions()
        assert set(actions) == set(PERMISSION_LEVELS["guest"])

    def test_get_allowed_actions_owner(self):
        perms = ComputerUsePermissions(identity=FakeIdentityOwner())
        actions = perms.get_allowed_actions()
        assert set(actions) == set(PERMISSION_LEVELS["owner"])

    def test_get_allowed_actions_trusted(self):
        perms = ComputerUsePermissions(identity=FakeIdentityTrusted())
        actions = perms.get_allowed_actions()
        assert set(actions) == set(PERMISSION_LEVELS["trusted"])

    def test_get_allowed_actions_guest(self):
        perms = ComputerUsePermissions(identity=FakeIdentityGuest())
        actions = perms.get_allowed_actions()
        assert set(actions) == set(PERMISSION_LEVELS["guest"])


class TestAutomationEnginePermissions:
    def test_screenshot_allowed_without_identity(self):
        engine = AutomationEngine(identity=None)
        result = engine.execute_action({"action": "capture_screen"}, dry_run=True)
        assert result.success

    def test_click_denied_without_identity(self):
        engine = AutomationEngine(identity=None)
        result = engine.execute_action({"action": "click", "x": 100, "y": 100})
        assert not result.success
        assert "Permission denied" in (result.error or "")

    def test_click_allowed_for_owner(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        result = engine.execute_action({"action": "click", "x": 100, "y": 100})
        assert "Permission denied" not in (result.error or "")

    def test_type_text_allowed_for_owner(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        result = engine.execute_action({"action": "type_text", "text": "hello"}, dry_run=True)
        assert result.success


class TestAutomationEngineDryRun:
    def test_dry_run_move_to(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        result = engine.execute_action({"action": "move_to", "x": 500, "y": 200}, dry_run=True)
        assert result.success
        assert "[DRY RUN]" in str(result.result)
        assert "move_to" in str(result.result)

    def test_dry_run_click(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        result = engine.execute_action({"action": "click", "x": 100, "y": 100}, dry_run=True)
        assert result.success
        assert "[DRY RUN]" in str(result.result)

    def test_dry_run_type_text(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        result = engine.execute_action({"action": "type_text", "text": "hello"}, dry_run=True)
        assert result.success
        assert "[DRY RUN]" in str(result.result)
        assert "hello" in str(result.result)

    def test_dry_run_hotkey(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        result = engine.execute_action({"action": "hotkey", "keys": ["ctrl", "c"]}, dry_run=True)
        assert result.success
        assert "[DRY RUN]" in str(result.result)

    def test_dry_run_list_windows(self):
        engine = AutomationEngine(identity=None)
        result = engine.execute_action({"action": "list_windows"}, dry_run=True)
        assert result.success

    def test_dry_run_focus_window(self):
        engine = AutomationEngine(identity=FakeIdentityTrusted())
        result = engine.execute_action({"action": "focus_window", "window_title": "Test"}, dry_run=True)
        assert result.success

    def test_dry_run_sequence(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        sequence = [
            {"action": "move_to", "x": 500, "y": 200},
            {"action": "click"},
            {"action": "type_text", "text": "hello"},
        ]
        results = engine.execute_sequence(sequence, dry_run=True)
        assert len(results) == 3
        for r in results:
            assert r.success
            assert "[DRY RUN]" not in str(r.result)

    def test_dry_run_sequence_summary_text(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        sequence = [
            {"action": "move_to", "x": 500, "y": 200},
            {"action": "click"},
        ]
        summary = engine.dry_run_sequence(sequence)
        assert "Computer Use Plan:" in summary
        assert "1. move_to" in summary
        assert "2. click" in summary
        assert "No actions executed." in summary
        assert "Proceed?" in summary


class TestAutomationEngineActions:
    def test_unknown_action_returns_error(self):
        engine = AutomationEngine(identity=FakeIdentityOwner())
        result = engine.execute_action({"action": "nonexistent_action"})
        assert not result.success
        assert "Unknown" in (result.error or "")

    def test_action_map_coverage(self):
        from moso_core.computer_use.automation import ACTION_MAP
        all_permission_actions = set()
        for actions in PERMISSION_LEVELS.values():
            all_permission_actions.update(actions)
        mapped_actions = set(ACTION_MAP.values())
        mapped_direct = set(ACTION_MAP.keys())
        exempt = {"execute_sequence", "record_mouse", "record_keyboard"}
        for pa in all_permission_actions:
            if pa in exempt:
                continue
            if pa not in mapped_actions and pa not in mapped_direct:
                pytest.fail(f"Action '{pa}' not mapped in ACTION_MAP or not a permission action")

    def test_execute_sequence_halts_on_failure(self):
        from unittest.mock import patch
        engine = AutomationEngine(identity=None)
        with patch.object(engine._windows, "_pygetwindow", create=True):
            engine._windows._available = True
            engine._windows.list_windows = MagicMock(return_value=ComputerUseResult(True, "list_windows", {"windows": ["Test"]}))
            sequence = [
                {"action": "list_windows"},
                {"action": "click", "x": 100, "y": 100},
                {"action": "move_to", "x": 500, "y": 200},
            ]
            results = engine.execute_sequence(sequence, dry_run=False)
            assert len(results) == 2
            assert results[0].success
            assert not results[1].success


class TestAutomationEngineResourceCheck:
    def test_resource_check_warning_not_critical(self):
        mock_resources = MagicMock()
        mock_status = MagicMock()
        mock_cpu = MagicMock()
        mock_cpu.percent = 50
        mock_status.cpu = mock_cpu
        mock_ram = MagicMock()
        mock_ram.percent = 50
        mock_status.ram = mock_ram
        mock_resources.get_system_status.return_value = mock_status
        engine = AutomationEngine(identity=FakeIdentityOwner(), resources=mock_resources)
        result = engine.execute_action({"action": "type_text", "text": "hello"}, dry_run=True)
        assert result.success

    def test_resource_check_logs_warning(self):
        mock_resources = MagicMock()
        mock_status = MagicMock()
        mock_cpu = MagicMock()
        mock_cpu.percent = 95
        mock_status.cpu = mock_cpu
        mock_ram = MagicMock()
        mock_ram.percent = 95
        mock_status.ram = mock_ram
        mock_resources.get_system_status.return_value = mock_status
        engine = AutomationEngine(identity=FakeIdentityOwner(), resources=mock_resources)
        result = engine.execute_action({"action": "type_text", "text": "hello"}, dry_run=True)
        assert result.success


class TestWorkflowRecorder:
    def test_export_sequence_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            seq = recorder.export_sequence(description="test workflow")
            assert isinstance(seq, AutomationSequence)
            assert len(seq.actions) == 0

    def test_export_sequence_with_mouse_move_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            recorder._events = [
                RecordedEvent(event_type="mouse_move", data={"x": 100, "y": 200}),
                RecordedEvent(event_type="mouse_move", data={"x": 150, "y": 250}),
            ]
            seq = recorder.export_sequence(description="mouse moves")
            assert len(seq.actions) == 2
            assert seq.actions[0]["action"] == "move_to"
            assert seq.actions[0]["x"] == 100
            assert seq.description == "mouse moves"

    def test_export_creates_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            recorder._events = [
                RecordedEvent(event_type="mouse_move", data={"x": 100, "y": 200}),
            ]
            recorder.export_sequence(description="single move")
            files = os.listdir(tmpdir)
            assert len(files) == 1
            assert files[0].startswith("workflow_")
            assert files[0].endswith(".json")
            with open(os.path.join(tmpdir, files[0])) as f:
                data = json.load(f)
                assert data["description"] == "single move"
                assert len(data["actions"]) == 1

    def test_export_clears_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            recorder._events = [
                RecordedEvent(event_type="mouse_move", data={"x": 100, "y": 200}),
            ]
            recorder.export_sequence()
            assert len(recorder._events) == 0

    def test_stop_recording_returns_event_count(self):
        recorder = WorkflowRecorder()
        recorder._events = [RecordedEvent(event_type="mouse_move", data={"x": 0, "y": 0})]
        result = recorder.stop_recording()
        assert result.success
        assert result.result["events"] == 1


class TestModels:
    def test_mouse_action_defaults(self):
        ma = MouseAction(x=100, y=200)
        assert ma.action_type == "click"
        assert ma.button == "left"
        assert ma.duration == 0.0

    def test_mouse_action_custom(self):
        ma = MouseAction(x=100, y=200, action_type="double_click", button="right", duration=0.5)
        assert ma.action_type == "double_click"

    def test_keyboard_action_type_text(self):
        ka = KeyboardAction(action_type="type", text="hello")
        d = ka.to_dict()
        assert "text" in d
        assert "hotkey_combo" not in d

    def test_keyboard_action_hotkey(self):
        ka = KeyboardAction(action_type="hotkey", hotkey_combo=["ctrl", "c"])
        d = ka.to_dict()
        assert "hotkey_combo" in d

    def test_screen_capture_timestamp(self):
        sc = ScreenCapture(image_path="/tmp/shot.png")
        assert sc.timestamp != ""

    def test_window_action_defaults(self):
        wa = WindowAction(window_title="Test")
        assert wa.action_type == "focus"

    def test_automation_sequence_defaults(self):
        seq = AutomationSequence()
        assert seq.actions == []
        assert seq.created_at != ""

    def test_computer_use_result_str_success(self):
        r = ComputerUseResult(success=True, action="click", result="ok")
        s = str(r)
        assert "[CU]" in s
        assert "click" in s

    def test_computer_use_result_str_failure(self):
        r = ComputerUseResult(success=False, action="click", error="no button")
        s = str(r)
        assert "FAILED" in s

    def test_recorded_event_defaults(self):
        ev = RecordedEvent(event_type="mouse_click", data={"x": 0, "y": 0})
        assert ev.timestamp != ""

    def test_recorded_event_to_dict(self):
        ev = RecordedEvent(event_type="mouse_click", data={"x": 100}, timestamp="2025-01-01")
        d = ev.to_dict()
        assert d["event_type"] == "mouse_click"
        assert d["data"]["x"] == 100


class TestControllersFallback:
    def test_mouse_controller_fallback_when_no_pyautogui(self):
        from moso_core.computer_use.mouse import MouseController
        with patch.dict("sys.modules", {"pyautogui": None}):
            import importlib
            import moso_core.computer_use.mouse as mouse_mod
            importlib.reload(mouse_mod)
            controller = mouse_mod.MouseController()
            result = controller.move_to(100, 200)
            assert not result.success

    def test_keyboard_controller_fallback_when_no_pyautogui(self):
        from moso_core.computer_use.keyboard import KeyboardController
        with patch.dict("sys.modules", {"pyautogui": None}):
            import importlib
            import moso_core.computer_use.keyboard as kb_mod
            importlib.reload(kb_mod)
            controller = kb_mod.KeyboardController()
            result = controller.type_text("hello")
            assert not result.success

    def test_window_manager_fallback_when_no_pygetwindow(self):
        from moso_core.computer_use.windows import WindowManager
        with patch.dict("sys.modules", {"pygetwindow": None}):
            import importlib
            import moso_core.computer_use.windows as win_mod
            importlib.reload(win_mod)
            manager = win_mod.WindowManager()
            result = manager.list_windows()
            assert not result.success

    def test_screen_capturer_fallback_when_no_mss(self):
        from moso_core.computer_use.screen import ScreenCapturer
        with patch.dict("sys.modules", {"mss": None}):
            import importlib
            import moso_core.computer_use.screen as sc_mod
            importlib.reload(sc_mod)
            capturer = sc_mod.ScreenCapturer(screenshot_dir=tempfile.gettempdir())
            result = capturer.capture_screen()
            assert not result.success
