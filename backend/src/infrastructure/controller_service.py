from __future__ import annotations

import threading

from src.controller.tool_controller import ToolController


class ControllerService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._controller = None
        return cls._instance

    def get_controller(self) -> ToolController:
        if self._controller is None:
            with self._lock:
                if self._controller is None:
                    self._controller = ToolController(num_history=10)
        return self._controller

    def reset_controller(self):
        with self._lock:
            self._controller = None

    def is_initialized(self) -> bool:
        return self._controller is not None


# Global instance
controller_service = ControllerService()
