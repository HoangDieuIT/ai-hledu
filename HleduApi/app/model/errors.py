from enum import Enum, auto
from typing import Any, Optional


def dauto(doc: str = ""):
    return auto(), doc


class Errorneous:
    def __init__(self, value, doc=None) -> None:
        self._doc = doc or ""

    @property
    def doc(self) -> str:
        return self._doc

    @property
    def value(self) -> Any:
        return self

    @property
    def detail(self) -> Any:
        return None

    @property
    def key(self) -> str:
        return self.name # type: ignore

    @property
    def message(self) -> str:
        return f"Service operation failed by {self.name}" # type: ignore

    @property
    def args(self) -> tuple:
        return ()

    @property
    def kwargs(self) -> dict[str, Any]:
        return {}

    def was(self, *candidates) -> bool:
        return any(map(lambda c: c is self.value, candidates))

    def on(self, __detail: Any = None, __message: Optional[str] = None, /, *args, **kwargs) -> 'DetailedErroneous':
        return DetailedErroneous(self, __detail, __message, *args, **kwargs)


class DetailedErroneous(Errorneous):
    def __init__(self, base: Errorneous, __detail: Any = None, __message: Optional[str] = None, /, *args, **kwargs) -> None:
        super().__init__(None)
        self._base = base
        self._detail = __detail
        self._message = __message
        self._args = args
        self._kwargs = kwargs

    @property
    def doc(self) -> str:
        return self._base.doc

    @property
    def value(self) -> Any:
        return self._base.value

    @property
    def detail(self) -> Any:
        return self._detail

    @property
    def key(self) -> str:
        return self._base.key

    @property
    def message(self) -> str:
        return (self._message and self._message.format(*self._args, **self._kwargs)) or str(self._detail)

    @property
    def args(self) -> tuple:
        return self._args

    @property
    def kwargs(self) -> dict[str, Any]:
        return self._kwargs


class Errors(Errorneous, Enum):
    #------------------------------------------------------------
    # service errors
    #------------------------------------------------------------
    # common
    IO_ERROR = dauto("Input/output error.")

    # account
    UNAUTHORIZED = dauto("Authentication failed.")
    NOT_SIGNED_UP = dauto("Sign up required.")

    # request
    INVALID_REQUEST = dauto("Invalid request.")

    # data
    DATA_NOT_FOUND = dauto("Data does not exist.")
    INVALID_IMAGE_FORMAT = dauto("Invalid image format.")

    # validations
    INVALID_CONTENT_TYPE = dauto("Invalid Content-Type.")
    INVALID_MULTIPART = dauto("Invalid multipart format.")