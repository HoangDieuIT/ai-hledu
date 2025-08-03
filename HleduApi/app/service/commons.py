from dataclasses import dataclass
from datetime import date, timedelta, timezone
from typing import Any, Optional

import app.model.composite as c
import app.model.db as m
from app.ext.custom_datetime import CustomDateTime as datetime
from app.model.errors import Errorneous, Errors
from app.resources import context as r
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import aliased, contains_eager

from .base import Maybe, service
