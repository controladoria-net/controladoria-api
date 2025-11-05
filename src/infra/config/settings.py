from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class AWSSettings:
    region: str
    bucket: str


@dataclass(frozen=True)
class SchedulerSettings:
    timezone: str
    batch_size: int
    external_rpm: int


@lru_cache(maxsize=1)
def get_aws_settings() -> AWSSettings:
    load_dotenv()
    region = os.getenv("AWS_REGION", "sa-east-1")
    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        raise RuntimeError(
            "S3_BUCKET environment variable is required for document storage."
        )
    return AWSSettings(region=region, bucket=bucket)


@lru_cache(maxsize=1)
def get_scheduler_settings() -> SchedulerSettings:
    load_dotenv()
    timezone = os.getenv("SCHED_TIMEZONE", "America/Sao_Paulo")
    batch_size = int(os.getenv("CRON_BATCH_SIZE", "20"))
    external_rpm = int(os.getenv("EXTERNAL_RPM", "60"))
    return SchedulerSettings(
        timezone=timezone, batch_size=batch_size, external_rpm=external_rpm
    )
