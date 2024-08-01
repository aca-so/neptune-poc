from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    release_version: str = Field('0.1.0', validation_alias='RELEASE_VERSION')
    api_key: str = Field(..., validation_alias='API_KEY')
    # Sentry
    sentry_sdk_key: str | None = Field(None, validation_alias='SENTRY_SDK_KEY')
    sentry_traces_sample_rate: float = Field(0.0, ge=0, validation_alias='SENTRY_TRACES_SAMPLE_RATE')
    # Neptune
    neptune_cluster_id: str = Field(..., validation_alias='NEPTUNE_CLUSTER_ID')
    neptune_region: str = Field(..., validation_alias='NEPTUNE_REGION')
    neptune_pool_size: int = Field(1, gt=0, validation_alias='NEPTUNE_POOL_SIZE')
    neptune_read_from_writer: bool = Field(True, validation_alias='NEPTUNE_READ_FROM_WRITER')
    neptune_recycle_conn_period: int = Field(5, gt=0, validation_alias='NEPTUNE_RECYCLE_CONN_PERIOD_IN_MINUTES')


settings = Settings()
