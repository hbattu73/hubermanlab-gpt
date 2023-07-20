from contextvars import ContextVar, copy_context
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class Globals:
    __slots__ = ("_vars", "_defaults")
    _vars: dict[str, ContextVar]
    _defaults: dict[str, Any]

    def __init__(self) -> None:
        object.__setattr__(self, '_vars', {})
        object.__setattr__(self, '_defaults', {})
    
    def cleanup(self):
        self._vars.clear()
        self._defaults.clear()
        del self._vars
        del self._defaults

    def set_default(self, name: str, default: Any) -> None:
        """Set a default value for a variable."""
        # Ignore if default is already set and is the same value
        if (name in self._defaults and default is self._defaults[name]):
            return
        # Ensure we don't have a value set already - the default will have no effect then
        if name in self._vars: 
            raise RuntimeError(f"Cannot set default as variable {name} was already set",)
        self._defaults[name] = default

    def _get_default_value(self, name: str) -> Any:
        default = self._defaults.get(name, None)
        return default() if callable(default) else default

    def _ensure_var(self, name: str) -> None:
        if name not in self._vars:
            default = self._get_default_value(name)
            self._vars[name] = ContextVar(f"globals:{name}", default=default)

    def __getattr__(self, name: str) -> Any:
        self._ensure_var(name)
        return self._vars[name].get()

    def __setattr__(self, name: str, value: Any) -> None:
        self._ensure_var(name)
        self._vars[name].set(value)
    
async def globals_middleware_dispatch(request: Request, call_next: Callable) -> Response:
    ctx = copy_context()
    def _call_next() -> Awaitable[Response]: return call_next(request)
    return await ctx.run(_call_next)

class GlobalsMiddleware(BaseHTTPMiddleware):  # noqa
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app, globals_middleware_dispatch)

g = Globals()

# REFERENCE: This one smart dude at https://gist.github.com/ddanier/ead419826ac6c3d75c96f9d89bea9bd0