from datetime import date, timedelta, timezone
from dataclasses import field, InitVar
from typing import Any, Optional, cast
from fastapi import APIRouter, Depends, Header, Query, Path, Request, Response, File, UploadFile, Body
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass
from app.model.errors import Errors
import app.model.db as m
import app.model.composite as c
from app.service.base import ServiceContext
from app.resources import context as r
from app.api.shared.auth import with_otp, maybe_otp, OTPAuthorized
from app.api.shared.errors import abort, abort_with, errorModel, ErrorResponse
from app.api.shared.dependencies import URLFor
from app.api.view import responses as vr
from app.api.view import requests as vq
from app.ext.custom_datetime import CustomDateTime as datetime