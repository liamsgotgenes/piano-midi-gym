"""MIDI device enumeration and input listener using mido + python-rtmidi."""

from __future__ import annotations
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional

import mido

from .theory import midi_to_pc


@dataclass
class MidiState:
    """Thread-safe snapshot of currently pressed MIDI notes."""

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _pressed: set[int] = field(default_factory=set)  # MIDI note numbers

    def note_on(self, note: int) -> None:
        with self._lock:
            self._pressed.add(note)

    def note_off(self, note: int) -> None:
        with self._lock:
            self._pressed.discard(note)

    def clear(self) -> None:
        with self._lock:
            self._pressed.clear()

    @property
    def pressed_notes(self) -> set[int]:
        with self._lock:
            return set(self._pressed)

    @property
    def pressed_pitch_classes(self) -> set[int]:
        with self._lock:
            return {midi_to_pc(n) for n in self._pressed}

    @property
    def lowest_pressed_note(self) -> Optional[int]:
        with self._lock:
            return min(self._pressed) if self._pressed else None


# Type for callbacks: receives (message_type, midi_note, velocity)
MidiCallback = Callable[[str, int, int], None]


class MidiInputManager:
    """Manages MIDI input port selection and event dispatching."""

    def __init__(self) -> None:
        self._port: Optional[mido.ports.BaseInput] = None
        self._port_name: Optional[str] = None
        self.state = MidiState()
        self._callbacks: list[MidiCallback] = []
        self._running = False

    @staticmethod
    def list_input_ports() -> list[str]:
        """Return available MIDI input port names."""
        try:
            return mido.get_input_names()
        except Exception:
            return []

    def open_port(self, port_name: str) -> None:
        """Open a MIDI input port by name and start listening."""
        self.close_port()
        self._port = mido.open_input(port_name, callback=self._on_message)
        self._port_name = port_name
        self._running = True

    def close_port(self) -> None:
        """Close the current MIDI input port."""
        if self._port is not None:
            self._running = False
            try:
                self._port.close()
            except Exception:
                pass
            self._port = None
            self._port_name = None
            self.state.clear()

    @property
    def is_open(self) -> bool:
        return self._port is not None and self._running

    @property
    def current_port_name(self) -> Optional[str]:
        return self._port_name

    def add_callback(self, cb: MidiCallback) -> None:
        """Register a callback for MIDI events: (type, note, velocity)."""
        self._callbacks.append(cb)

    def remove_callback(self, cb: MidiCallback) -> None:
        self._callbacks = [c for c in self._callbacks if c is not cb]

    def _on_message(self, msg: mido.Message) -> None:
        """Internal callback from mido — runs on mido's listener thread."""
        if not self._running:
            return

        if msg.type == "note_on" and msg.velocity > 0:
            self.state.note_on(msg.note)
            self._dispatch("note_on", msg.note, msg.velocity)
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            self.state.note_off(msg.note)
            self._dispatch("note_off", msg.note, 0)

    def _dispatch(self, msg_type: str, note: int, velocity: int) -> None:
        for cb in self._callbacks:
            try:
                cb(msg_type, note, velocity)
            except Exception:
                pass
