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


@dataclass(frozen=True)
class ConcurrencySettings:
    max_classify_workers: int
    max_extract_workers: int
    ia_max_in_flight: int


@dataclass(frozen=True)
class RetrySettings:
    max_attempts: int
    wait_initial: float
    wait_max: float
    ia_timeout_seconds: float


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


@lru_cache(maxsize=1)
def get_concurrency_settings() -> ConcurrencySettings:
    load_dotenv()
    return ConcurrencySettings(
        max_classify_workers=int(os.getenv("MAX_CLASSIFY_WORKERS", "4")),
        max_extract_workers=int(os.getenv("MAX_EXTRACT_WORKERS", "6")),
        ia_max_in_flight=int(os.getenv("IA_MAX_IN_FLIGHT", "4")),
    )


@lru_cache(maxsize=1)
def get_retry_settings() -> RetrySettings:
    load_dotenv()
    return RetrySettings(
        max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
        wait_initial=float(os.getenv("RETRY_INITIAL", "0.5")),
        wait_max=float(os.getenv("RETRY_MAX", "10")),
        ia_timeout_seconds=float(os.getenv("IA_TIMEOUT_SECONDS", "30")),
    )
