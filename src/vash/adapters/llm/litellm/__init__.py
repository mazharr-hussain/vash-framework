"""The model gateway (LiteLLM proxy on the VM): VASH's client for it, and the settings VASH writes for it."""
from .adapter import Adapter

__all__ = ["Adapter"]
