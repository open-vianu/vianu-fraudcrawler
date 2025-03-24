import logging

from src.settings import LOG_FMT, LOG_LVL
from src.base import Setup, Host, Location, Language

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT)
logger = logging.getLogger(__name__)

def test_setup():
    setup = Setup()
    assert setup.serpapi_key
    assert setup.dataforseo_user
    assert setup.dataforseo_pwd
    assert setup.zyteapi_key
    assert setup.openaiapi_key


def test_host():
    host = Host(name="Galaxus", domains="galaxus.ch, digitec.ch,example.com")
    assert host.name == "Galaxus"
    assert host.domains == ["galaxus.ch", "digitec.ch", "example.com"]

    host = Host(name="Galaxus", domains=["galaxus.ch", "digitec.ch", "example.com"])
    assert host.name == "Galaxus"
    assert host.domains == ["galaxus.ch", "digitec.ch", "example.com"]


def test_location():
    location = Location(name="Switzerland", code="ch")
    assert location.name == "Switzerland"
    assert location.code == "ch"

    location = Location(name="switzerland", code="CH")
    assert location.name == "switzerland"
    assert location.code == "ch"


def test_language():
    language = Language(name="German", code="de")
    assert language.name == "German"
    assert language.code == "de"

    language = Language(name="german", code="DE")
    assert language.name == "german"
    assert language.code == "de"