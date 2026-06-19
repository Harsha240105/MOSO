from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional


@dataclass
class BoundingBox:
    left: int
    top: int
    width: int
    height: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OCRResult:
    text: str
    confidence: float
    bounding_box: BoundingBox

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box.to_dict(),
        }


@dataclass
class WindowInfo:
    title: str
    active: bool = False
    bounds: tuple[int, int, int, int] | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class ScreenContext:
    timestamp: str = ""
    resolution: tuple[int, int] = (0, 0)
    active_window: str = ""
    windows: list[str] = field(default_factory=list)
    text_content: str = ""
    ocr_results: list[OCRResult] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "resolution": list(self.resolution),
            "active_window": self.active_window,
            "windows": list(self.windows),
            "text_content": self.text_content,
            "ocr_results": [r.to_dict() for r in self.ocr_results],
        }

    def summary(self) -> str:
        lines = [f"Active Window: {self.active_window}"]
        if self.windows:
            lines.append(f"Open Windows ({len(self.windows)}):")
            for w in self.windows[:10]:
                marker = " *" if w == self.active_window else ""
                lines.append(f"  - {w}{marker}")
        if self.text_content:
            text_preview = self.text_content[:200].replace("\n", " ")
            if len(self.text_content) > 200:
                text_preview += "..."
            lines.append(f"Visible Text: {text_preview}")
        lines.append(f"Resolution: {self.resolution[0]}x{self.resolution[1]}")
        return "\n".join(lines)
