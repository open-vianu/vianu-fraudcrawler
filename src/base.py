from pydantic_settings import BaseSettings


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