"""State management for tracking article changes."""
import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from .models import SourceState


class StateManager:
    """Manages persistent state for each monitored source."""

    def __init__(self, state_dir: str = "state"):
        """Initialize state manager.

        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_state_file(self, source_id: str) -> Path:
        """Get the state file path for a source."""
        return self.state_dir / f"{source_id}.json"

    def load_state(self, source_id: str) -> SourceState:
        """Load state for a source.

        Args:
            source_id: Unique identifier for the source

        Returns:
            SourceState object (new if file doesn't exist)
        """
        state_file = self._get_state_file(source_id)

        if not state_file.exists():
            return SourceState(source_id=source_id)

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SourceState.from_dict(data)
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Warning: Could not load state for {source_id}: {e}")
            return SourceState(source_id=source_id)

    def save_state(self, state: SourceState) -> None:
        """Save state for a source.

        Args:
            state: SourceState object to save
        """
        state_file = self._get_state_file(state.source_id)

        # Update last checked timestamp
        state.last_checked = datetime.utcnow().isoformat() + "Z"

        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save state for {state.source_id}: {e}")
