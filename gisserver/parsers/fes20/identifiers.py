"""These classes map to the FES 2.0 specification for identifiers.
The class names are identical to those in the FES spec.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from django.db.models import Q
from django.utils.functional import cached_property

from gisserver.parsers.base import BaseNode, FES20, tag_registry
from gisserver.parsers.utils import auto_cast, get_attribute, parse_iso_datetime

NoneType = type(None)


class VersionActionTokens(Enum):
    FIRST = "FIRST"
    LAST = "LAST"
    ALL = "ALL"
    NEXT = "NEXT"
    PREVIOUS = "PREVIOUS"


class Id(BaseNode):
    """Abstract base class, as defined by FES spec."""

    xml_ns = FES20

    def build_query(self, fesquery) -> Q:
        raise NotImplementedError()

    @property
    def type_name(self):
        """Tell which typename this ID applies to"""
        raise NotImplementedError()


@dataclass
@tag_registry.register("ResourceId")
class ResourceId(Id):
    """The <fes:ResourceId> element."""

    rid: str
    version: Union[int, datetime, VersionActionTokens, NoneType] = None
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None

    @cached_property
    def _rid_parts(self):
        return self.rid.rsplit(".", 1)

    @property
    def type_name(self):
        return self._rid_parts[0]

    @property
    def id(self):
        return self._rid_parts[1]

    @classmethod
    def from_xml(cls, element):
        version = element.get("version")
        startTime = element.get("startTime")
        endTime = element.get("endTime")

        if version:
            version = auto_cast(version)

        return cls(
            rid=get_attribute(element, "rid"),
            version=version,
            startTime=parse_iso_datetime(startTime) if startTime else None,
            endTime=parse_iso_datetime(endTime) if endTime else None,
        )

    def build_query(self, fesquery) -> Q:
        """Render the SQL filter"""
        if self.startTime or self.endTime or self.version:
            raise NotImplementedError(
                "No support for <fes:ResourceId> startTime/endTime/version attributes"
            )

        # NOTE: type_name is currently read by the IdOperator that contains this object.
        return Q(pk=self.id)
