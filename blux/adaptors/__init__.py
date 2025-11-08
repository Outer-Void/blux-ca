# Adaptors package
from .dummy_local import DummyLocalAdaptor

try:  # Optional HTTP adaptor dependency
    from .http_api_adaptor import HTTPAPIAdaptor
except ModuleNotFoundError:  # pragma: no cover - optional flask integration
    HTTPAPIAdaptor = None  # type: ignore

__all__ = ["DummyLocalAdaptor", "HTTPAPIAdaptor"]