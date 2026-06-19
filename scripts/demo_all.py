from __future__ import annotations

import os
import sys
import tempfile

from moso_core.memory.manager import MemoryManager
from moso_core.resources.manager import ResourceManager
from moso_core.tools.registry import ToolRegistry
from moso_core.tools.file_tool import FileTool
from moso_core.tools.app_tool import AppTool
from moso_core.tools.browser_tool import BrowserTool
from moso_core.tools.terminal_tool import TerminalTool
from moso_core.tools.models import ToolRequest
from moso_core.agents.manager import AgentManager
from moso_core.computer_use.automation import AutomationEngine
from moso_core.vision.manager import VisionManager


def sep(title):
    print()
    print("=" * 65)
    print(f"  {title}")
    print("=" * 65)


def safe(text):
    """Return ascii-safe version of text."""
    if text is None:
        return ""
    return text.encode("ascii", errors="replace").decode("ascii")


def demo_memory():
    sep("MEMORY ENGINE")
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    with MemoryManager(db_path=db) as mm:
        mm.store_event("Ran MOSO demo", "First full system demo")
        mm.store_event("Chatted about Python", "Discussing Python features")
        mm.store_fact("User likes Python", category="preference")
        mm.store_procedure("Run tests", ["cd MOSO", "pytest"], tags=["testing"])
        mm.store_preference("editor", "VS Code")
        recent = mm.retrieve_recent_events(3)
        print(f"  Recent events: {[e.title for e in recent]}")
        facts = mm.retrieve_memories("Python", memory_types=["semantic"])
        print(f"  Semantic search: {len(facts.get('semantic', []))} result(s)")
        prefs = mm.retrieve_preferences()
        print(f"  Preferences: {[(p.category, p.value) for p in prefs]}")
    print("  OK - Memory")


def demo_resources():
    sep("RESOURCE MANAGER")
    rm = ResourceManager()
    cpu = rm.get_cpu()
    print(f"  CPU: {cpu.usage_percent}% ({cpu.cores}C/{cpu.threads}T)")
    ram = rm.get_ram()
    print(f"  RAM: {ram.used / 1e9:.1f}GB / {ram.total / 1e9:.1f}GB ({ram.percent}%)")
    storage = rm.get_storage()
    if storage:
        m = storage[0]
        print(f"  Disk: {m.mount_point} - {m.used / 1e9:.0f}GB / {m.total / 1e9:.0f}GB ({m.percent}%)")
    bat = rm.get_battery()
    if bat:
        print(f"  Battery: {bat.percent}% {'(plugged)' if bat.plugged_in else '(on battery)'}")
    net = rm.get_network()
    print(f"  Network up/down: {net.bytes_sent / 1e6:.1f}MB / {net.bytes_recv / 1e6:.1f}MB")
    top = rm.get_top_cpu_processes(3)
    print(f"  Top CPU: {[safe(p.name) for p in top]}")
    print("  OK - Resources")


def demo_tools():
    sep("TOOL ENGINE")
    registry = ToolRegistry()
    registry.register_tool(FileTool())
    registry.register_tool(AppTool())
    registry.register_tool(BrowserTool())
    registry.register_tool(TerminalTool())
    print(f"  Tools: {[t['name'] for t in registry.list_tools()]}")
    result = registry.execute_tool(ToolRequest(
        tool_name="file_tool",
        parameters={"action": "list_directory", "path": "."},
    ))
    print(f"  file_tool: success={result.success}")
    items = result.result if isinstance(result.result, list) else []
    print(f"  Found {len(items)} items")
    dry = registry.execute_tool(ToolRequest(
        tool_name="file_tool",
        parameters={"action": "delete_file", "path": "nope.txt"},
        dry_run=True,
    ))
    print(f"  Dry-run: {safe(str(dry.result))}")
    print("  OK - Tools")


def demo_agents():
    sep("AGENT PLANNER")
    am = AgentManager()
    templates = am.list_templates()
    print(f"  {len(templates)} templates:")
    for t in templates:
        print(f"    - {t['name']}: {t['description']}")
    plan = am.preview_plan("create a python project called demo")
    print(f"  Plan preview:\n  {safe(plan).replace(chr(10), chr(10)+'  ')}")
    plan2 = am.preview_plan("screenshot the screen")
    print(f"  Desktop automation:\n  {safe(plan2).replace(chr(10), chr(10)+'  ')}")
    print("  OK - Agents")


def demo_computer_use():
    sep("COMPUTER USE")
    ae = AutomationEngine()
    dry = ae.dry_run_sequence([
        {"action": "move_to", "x": 500, "y": 300},
        {"action": "click"},
        {"action": "type_text", "text": "MOSO demo"},
    ])
    print(f"  Dry-run:\n  {safe(dry).replace(chr(10), chr(10)+'  ')}")
    windows = ae.execute_action({"action": "list_windows"})
    if windows.success:
        w = windows.result if isinstance(windows.result, list) else windows.result.get("windows", [])
        print(f"  Windows ({len(w)}): {[safe(str(x)) for x in w[:5]]}")
    else:
        print(f"  list_windows: {windows.error}")
    print("  OK - Computer Use")


def demo_vision():
    sep("SCREEN VISION")
    vm = VisionManager()
    active = vm.get_active_window()
    print(f"  Active window: {safe(active) or '(none)'}")
    text = vm.get_screen_text()
    print(f"  Screen text: {len(text)} chars - {safe(text[:60]) if text else '(none)'}")
    ctx = vm.build_context()
    print(f"  Resolution: {ctx.resolution}")
    print(f"  Windows: {[safe(str(w)) for w in ctx.windows[:5]]}")
    print("  OK - Vision")


def main():
    print()
    print("  " + "#" * 55)
    print("  #              MOSO AI -- LOCAL DEMO                   #")
    print("  #  All components running on-device, no cloud calls   #")
    print("  " + "#" * 55)

    modules = [
        ("Memory", demo_memory),
        ("Resources", demo_resources),
        ("Tools", demo_tools),
        ("Agents", demo_agents),
        ("Computer Use", demo_computer_use),
        ("Vision", demo_vision),
    ]

    for name, fn in modules:
        try:
            fn()
        except Exception as e:
            print(f"  !! {name}: {safe(str(e))}")

    print()
    print("  " + "#" * 55)
    print("  #  All 6 modules ran on your laptop.                  #")
    print("  #  Add LLM: install llama-cpp-python then             #")
    print("  #    Orchestrator(model_path='path/to/model.gguf')    #")
    print("  " + "#" * 55)
    print()


if __name__ == "__main__":
    main()
