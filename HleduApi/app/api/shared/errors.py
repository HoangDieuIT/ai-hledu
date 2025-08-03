from collections.abc import Callable
from configparser import ConfigParser
from dataclasses import field
from dataclasses import dataclass as builtin_dataclass
import logging
from typing import Any, Literal, Union, Optional, NoReturn, cast
from typing_extensions import Self
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler as default_handler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from pydantic import ValidationError, Field
from pydantic.dataclasses import dataclass
from pydantic_core import ErrorDetails
from app.model.errors import Errorneous
from .i18n import I18N


#----------------------------------------------------------------
# Response types
#----------------------------------------------------------------
@dataclass
class ErrorResponse:
    """
    Common response for errors.
    """
    code: str = Field(description="Error code.")
    message: str = Field(description="Error message.")
    args: list[Any] = Field(default_factory=list, description="Arguments for error message formatting.")
    kwargs: dict[str, Any] = Field(default_factory=dict, description="Keyword arguments for error message formatting.")
    detail: Any = Field(default=None, description="Detailed information.")

    def localize(self, formatter: Callable[[str], str | None]) -> Self:
        """
        Changes the error message by localization.

        Args:
            formatter: Function to get message format from error code.
        Returns:
            This instance after localization.
        """
        fmt = formatter(self.code)
        if fmt:
            self.message = fmt.format(*self.args or [], **self.kwargs or {})
        return self


@dataclass
class ValidationDetail:
    """
    Detailed information for each field of validation errors.
    """
    loc: list[str | int] = Field(description="Path of the field where the error occurred.")
    type: str = Field(description="Type of error.")
    message: str = Field(description="Error message.")
    kwargs: dict[str, Any] = Field(description="Keyword arguments for error message formatting.")

    @classmethod
    def from_error(cls, err: ErrorDetails) -> Self:
        """
        Generates from Pydantic's validation error detail object.
        """
        return ValidationDetail(
            loc=list(err["loc"]),
            type=err["type"],
            message=err["msg"],
            kwargs=cast(dict[str, Any], err["ctx"]) if "ctx" in err else {},
        )


@dataclass
class ValidationErrorResponse(ErrorResponse):
    """
    Response for validation errors.
    """
    code: Literal['validation_error'] = Field(description="Error code.")
    detail: list[ValidationDetail] = Field(default_factory=list, description="Error list.")

    def localize(self, formatter: Callable[[str], str | None]) -> Self:
        super().localize(formatter)
        for err in self.detail:
            fmt = formatter(err.type)
            if fmt:
                err.message = fmt.format(**err.kwargs or {})
        return self


#----------------------------------------------------------------
# Application errors
#----------------------------------------------------------------
@builtin_dataclass
class HTTPApplicationError(Exception):
    """
    Errors generated within the application.
    """
    status: int
    error: ErrorResponse
    cause: Exception | None = None


def abort(status: int, cause: Any = None, code: Optional[str] = None, message: Optional[str] = None, *args, **kwargs) -> NoReturn:
    """
    Raises an error from the application.

    Args:
        status: HTTP status code.
        cause: Object such as an exception that caused the error.
        code: Error code. If omitted, `unexpected` is set.
        message: Error message. If omitted, `Internal server error` is set.
    """
    if isinstance(cause, Errorneous):
        raise HTTPApplicationError(status=status, error=ErrorResponse(
            code=(code or cause.key).lower(),
            message=message or cause.message,
            args=(list(cause.args) if cause.args else []) + list(args),
            kwargs=(cause.kwargs or {}) | kwargs,
            detail=None,
        ), cause=cause.detail if isinstance(cause.detail, Exception) else None)
    else:
        raise HTTPApplicationError(status=status, error=ErrorResponse(
            code=(code or "unexpected").lower(),
            message=message or (cause and str(cause)) or "Internal server error",
            args=list(args),
            kwargs=kwargs,
        ))


def abort_with(status: int, code: Optional[str] = None, message: Optional[str] = None) -> Callable[[Any], NoReturn]:
    """
    Gets a function that receives an error object and calls `abort`.

    Args:
        status: HTTP status code.
        code: Error code. If omitted, `unexpected` is set.
        message: Error message. If omitted, `Internal server error` is set.
    Returns:
        A function that receives an error object and raises an application error.
    """
    def inner(cause: Any = None):
        abort(status, cause, code, message)
    return inner


def errorModel(*errors: Union[Errorneous, tuple[str, str], Any], model_index: list[int] = [0]) -> type:
    """
    Receives a list of objects indicating errors and generates a type to output as a table in the document.

    Args:
        errors: List of objects indicating errors.
    Returns:
        A type that summarizes the given errors.
    """
    def table(*errors) -> str:
        if not errors:
            return ""

        def row(e) -> str:
            if isinstance(e, Errorneous):
                return f"|`{e.name.lower()}`|{e.doc}|" # type: ignore
            elif isinstance(e, tuple):
                return f"|`{e[0]}`|{e[1] if len(e) > 1 else ''}|"
            else:
                return f"|`{str(e)}`||"

        rows = '\n'.join(row(e) for e in errors)

        return f"""

| code | description |
| :--- | :--- |
{rows}
"""

    # class name must be unique because pydantic maps types by their names.
    # class definition syntax does not work maybe because the dataclass is wrapped by pydantic model type.
    model = type(
        f"ErrorResponse_{model_index[0]}",
        (ErrorResponse,),
        dict(code = field(metadata=dict(description="Error code."+table(*errors)))),
    )
    model.__annotations__["code"] = str
    model = dataclass(model)
    model_index[0] += 1
    return model


#----------------------------------------------------------------
# Activation
#----------------------------------------------------------------
def setup_handlers(
    app: FastAPI,
    msg: Union[str, list[str], None],
    logger: logging.Logger,
):
    """
    Sets up error handlers.

    Args:
        app: Application.
        msg: Path to message file(s) in `ConfigParser` format.
        logger: Error output logger.
    """
    # Localization
    messages = ConfigParser()
    if msg:
        messages.read(msg)
    available_langs = messages.sections()

    def formatter(req: Request) -> Callable[[str], str | None]:
        def format(code: str) -> str | None:
            i18n = I18N(req.headers.getlist("Accept-Language"))
            lang = i18n.lookup(available_langs)
            section = messages[lang.value if lang else 'DEFAULT']
            return section[code] if code in section else None
        return format

    @app.exception_handler(HTTPException)
    async def http_exception_handler(req: Request, exc: HTTPException):
        if exc.status_code == 401:
            return await default_handler(req, exc)
        logger.warning(f"An unexpected exception was thrown.", exc_info=exc)
        err = ErrorResponse(code="unexpected", message=str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(err.localize(formatter(req))))

    @app.exception_handler(ValidationError)
    async def request_validation_handler(req: Request, exc: ValidationError):
        err = ValidationErrorResponse(
            code="validation_error",
            message=f"Validations failed on {len(exc.errors())} fields.",
            detail=[ValidationDetail.from_error(e) for e in exc.errors()],
        )
        return JSONResponse(status_code=422, content=jsonable_encoder(err.localize(formatter(req))))

    @app.exception_handler(RequestValidationError)
    async def response_validation_handler(req: Request, exc: RequestValidationError):
        logger.warning(f"Invalid response data raised an error.", exc_info=exc)
        err = ErrorResponse(code="unexpected", message="Internal server error.")
        return JSONResponse(status_code=500, content=jsonable_encoder(err.localize(formatter(req))))

    @app.exception_handler(HTTPApplicationError)
    async def application_error_handler(req: Request, exc: HTTPApplicationError):
        if exc.cause:
            logger.warning(f"An unexpected exception was thrown.", exc_info=exc.cause)
        return JSONResponse(status_code=exc.status, content=jsonable_encoder(exc.error.localize(formatter(req))))
