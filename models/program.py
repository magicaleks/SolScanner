from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProgramTwitterData(BaseModel):

    link: str
    followers: Optional[int] = 0


class ProgramTelegramData(ProgramTwitterData):
    pass


class ProgramWebsiteData(BaseModel):

    link: str
    created_at: Optional[datetime] = None


class Program(BaseModel):

    title: str
    address: str
    cap: float
    liq: float
    link: str
    icon: Optional[str] = ""
    description: Optional[str] = ""
    symbol: Optional[str] = ""
    developer: Optional[str] = ""
    twitter: Optional[ProgramTwitterData] = None
    telegram: Optional[ProgramTelegramData] = None
    website: Optional[ProgramWebsiteData] = None
    listing: Optional[datetime] = None
