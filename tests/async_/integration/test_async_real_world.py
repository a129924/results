"""Integration tests for AsyncResult in realistic scenarios."""

import asyncio
from typing import Any

import pytest

from results import AsyncResult, Err, Ok, Result


async def fetch_patient(patient_id: str) -> Result[dict[str, Any], str]:
    await asyncio.sleep(0)
    if patient_id == "missing":
        return Err("patient not found")
    return Ok({"id": patient_id, "active": True})


async def fetch_latest_observation(
    patient: dict[str, Any],
) -> Result[dict[str, Any], str]:
    await asyncio.sleep(0)
    if not patient.get("active"):
        return Err("patient inactive")
    return Ok({"patient_id": patient["id"], "value": 120})


async def enrich_observation(obs: dict[str, Any]) -> dict[str, Any]:
    await asyncio.sleep(0)
    return {**obs, "units": "mmHg"}


async def persist_observation(obs: dict[str, Any]) -> Result[dict[str, Any], Any]:
    await asyncio.sleep(0)
    return Ok(obs | {"persisted": True})


@pytest.mark.asyncio
async def test_happy_path_chain() -> None:
    res = (
        AsyncResult.from_awaitable(fetch_patient("123"))
        .and_then_async(fetch_latest_observation)
        .map_async(enrich_observation)
        .and_then_async(persist_observation)
    )

    inner = await res
    result_dict = inner.ok()
    assert result_dict is not None
    assert result_dict["persisted"] is True
    assert result_dict["units"] == "mmHg"


@pytest.mark.asyncio
async def test_failure_short_circuits_and_keeps_context() -> None:
    res = (
        AsyncResult.from_awaitable(fetch_patient("missing"))
        .context("fetch patient")
        .and_then_async(fetch_latest_observation)
        .context("fetch latest obs")
        .map_async(enrich_observation)
    )

    inner = await res
    assert inner.is_err()
    assert inner.err() == "patient not found"
