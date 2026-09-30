from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = (
        "postgresql+psycopg://cocotrade:cocotrade@localhost:5432/cocotrade"
    )
    typesafe_api_key: str | None = None
    # api.binance.com은 일부 국가(미국 포함)에서 451을 반환한다. 공개 시세 전용 도메인은 열려 있다.
    binance_public_url: str = "https://data-api.binance.vision/api/v3"
    # 원숭이 전략을 나눠 돌릴 프로세스 수
    backtest_workers: int = 4


settings = Settings()
