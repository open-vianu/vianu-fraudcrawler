from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings
from typing import List


class Setup(BaseSettings):
    """Class for loading environment variables."""

    # Crawler ENV variables
    serpapi_key: str
    dataforseo_user: str
    dataforseo_pwd: str
    zyteapi_key: str
    openaiapi_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Host(BaseModel):
    """Model for host details (e.g. `Host(name="Galaxus", domains="galaxus.ch, digitec.ch")`)."""
    name: str
    domains: str | List[str]

    @field_validator('domains', mode='before')
    def split_domains_if_str(cls, val):
        if isinstance(val, str):
            return [dom.strip() for dom in val.split(',')]
        return val


class Location(BaseModel):
    """Model for location details (e.g. `Location(name="Switzerland", code="ch")`)."""
    name: str
    code: str

    @field_validator('code', mode='before')
    def lower_code(cls, val):
        return val.lower()


class Language(BaseModel):
    """Model for language details (e.g. `Language(name="German", code="de")`)."""
    name: str
    code: str

    @field_validator('code', mode='before')
    def lower_code(cls, val):
        return val.lower()


class Keyword(BaseModel):
    text: str
    volume: int
