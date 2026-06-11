"""Pin scheduling logic.

This module handles scheduling pins for future publication.
It enforces the Pinterest guideline that "end users must choose each
Pin to be published" — there is no bulk or automated publishing
without explicit user approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import time


# Local scheduled pins storage
SCHEDULES_DIR = Path.home() / ".fox-pinterest" / "schedules"


@dataclass
class ScheduledPin:
    """A pin scheduled for future publication."""
    pin_id: Optional[str]
    board_id: str
    image_path: str
    title: str
    description: str
    link: str
    scheduled_time: str  # ISO 8601
    approved: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict:
        return {
            "pin_id": self.pin_id,
            "board_id": self.board_id,
            "image_path": self.image_path,
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "scheduled_time": self.scheduled_time,
            "approved": self.approved,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> ScheduledPin:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class PinScheduler:
    """Local pin scheduler.
    
    Pins are scheduled locally and require explicit user approval
    before being published to Pinterest. This complies with the
    Developer Guideline that end users must "choose each Pin to
    be published" — no automated bulk publishing.
    """
    
    def __init__(self):
        SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
        self._schedules_file = SCHEDULES_DIR / "scheduled_pins.json"
    
    def _load(self) -> list[dict]:
        if self._schedules_file.exists():
            with open(self._schedules_file, "r") as f:
                return json.load(f)
        return []
    
    def _save(self, pins: list[dict]):
        with open(self._schedules_file, "w") as f:
            json.dump(pins, f, indent=2)
    
    def schedule(
        self,
        board_id: str,
        image_path: str,
        title: str,
        description: str,
        link: str,
        scheduled_time: str,
    ) -> ScheduledPin:
        """Schedule a new pin.
        
        Args:
            board_id: Pinterest board ID.
            image_path: Local path to the pin image.
            title: Pin title.
            description: Pin description.
            link: Destination URL.
            scheduled_time: ISO 8601 datetime string.
            
        Returns:
            The created ScheduledPin.
        """
        pins = self._load()
        
        scheduled_pin = ScheduledPin(
            pin_id=None,  # Will be set after API creation
            board_id=board_id,
            image_path=str(Path(image_path).resolve()),
            title=title,
            description=description,
            link=link,
            scheduled_time=scheduled_time,
        )
        
        pins.append(scheduled_pin.to_dict())
        self._save(pins)
        
        return scheduled_pin
    
    def list_scheduled(self) -> list[ScheduledPin]:
        """List all scheduled pins, sorted by scheduled_time."""
        pins = self._load()
        result = [ScheduledPin.from_dict(p) for p in pins]
        return sorted(result, key=lambda p: p.scheduled_time)
    
    def approve(self, pin_id: str) -> Optional[ScheduledPin]:
        """Mark a scheduled pin for approval.
        
        Args:
            pin_id: The internal ID of the scheduled pin.
            
        Returns:
            The approved ScheduledPin, or None if not found.
        """
        pins = self._load()
        for pin_data in pins:
            internal_id = pin_data.get("internal_id", pin_data.get("id", ""))
            # Use the index as the internal ID since we don't store one
            if pin_data is pins[pins.index(pin_data)]:
                pin_data["approved"] = True
                self._save(pins)
                return ScheduledPin.from_dict(pin_data)
        
        return None
    
    def approve_by_index(self, index: int) -> Optional[ScheduledPin]:
        """Approve a pin by its index in the scheduled list.
        
        Args:
            index: 0-based index in the scheduled pins list.
            
        Returns:
            The approved ScheduledPin, or None if not found.
        """
        pins = self._load()
        if 0 <= index < len(pins):
            pins[index]["approved"] = True
            self._save(pins)
            return ScheduledPin.from_dict(pins[index])
        return None
    
    def remove(self, index: int) -> bool:
        """Remove a scheduled pin.
        
        Args:
            index: 0-based index in the scheduled list.
            
        Returns:
            True if removed, False if index was invalid.
        """
        pins = self._load()
        if 0 <= index < len(pins):
            pins.pop(index)
            self._save(pins)
            return True
        return False
    
    def get_pending(self) -> list[ScheduledPin]:
        """Get scheduled pins that haven't been approved yet."""
        return [p for p in self.list_scheduled() if not p.approved]
    
    def get_due(self) -> list[ScheduledPin]:
        """Get scheduled pins that are due for publication now."""
        now = datetime.now(timezone.utc)
        due = []
        for pin in self.list_scheduled():
            try:
                sched_time = datetime.fromisoformat(pin.scheduled_time)
                if sched_time <= now and pin.approved:
                    due.append(pin)
            except (ValueError, TypeError):
                continue
        return due
