"""Tests for the Risco binary sensors."""
from unittest.mock import PropertyMock, patch

import pytest

from homeassistant.components.risco import CannotConnectError, UnauthorizedError
from homeassistant.components.risco.const import DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity

from .util import TEST_SITE_UUID

FIRST_ENTITY_ID = "binary_sensor.zone_0"
SECOND_ENTITY_ID = "binary_sensor.zone_1"
FIRST_ALARMED_ENTITY_ID = FIRST_ENTITY_ID + "_alarmed"
SECOND_ALARMED_ENTITY_ID = SECOND_ENTITY_ID + "_alarmed"


@pytest.mark.parametrize("exception", [CannotConnectError, UnauthorizedError])
async def test_error_on_login(hass, login_with_error, cloud_config_entry):
    """Test error on login."""
    await hass.config_entries.async_setup(cloud_config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert not registry.async_is_registered(FIRST_ENTITY_ID)
    assert not registry.async_is_registered(SECOND_ENTITY_ID)


async def test_cloud_setup(hass, two_zone_cloud, setup_risco_cloud):
    """Test entity setup."""
    registry = er.async_get(hass)
    assert registry.async_is_registered(FIRST_ENTITY_ID)
    assert registry.async_is_registered(SECOND_ENTITY_ID)

    registry = dr.async_get(hass)
    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_zone_0")})
    assert device is not None
    assert device.manufacturer == "Risco"

    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_zone_1")})
    assert device is not None
    assert device.manufacturer == "Risco"


async def _check_cloud_state(hass, zones, triggered, entity_id, zone_id):
    with patch.object(
        zones[zone_id],
        "triggered",
        new_callable=PropertyMock(return_value=triggered),
    ):
        await async_update_entity(hass, entity_id)
        await hass.async_block_till_done()

        expected_triggered = STATE_ON if triggered else STATE_OFF
        assert hass.states.get(entity_id).state == expected_triggered
        assert hass.states.get(entity_id).attributes["zone_id"] == zone_id


async def test_cloud_states(hass, two_zone_cloud, setup_risco_cloud):
    """Test the various alarm states."""
    await _check_cloud_state(hass, two_zone_cloud, True, FIRST_ENTITY_ID, 0)
    await _check_cloud_state(hass, two_zone_cloud, False, FIRST_ENTITY_ID, 0)
    await _check_cloud_state(hass, two_zone_cloud, True, SECOND_ENTITY_ID, 1)
    await _check_cloud_state(hass, two_zone_cloud, False, SECOND_ENTITY_ID, 1)


@pytest.mark.parametrize("exception", [CannotConnectError, UnauthorizedError])
async def test_error_on_connect(hass, connect_with_error, local_config_entry):
    """Test error on connect."""
    await hass.config_entries.async_setup(local_config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert not registry.async_is_registered(FIRST_ENTITY_ID)
    assert not registry.async_is_registered(SECOND_ENTITY_ID)
    assert not registry.async_is_registered(FIRST_ALARMED_ENTITY_ID)
    assert not registry.async_is_registered(SECOND_ALARMED_ENTITY_ID)


async def test_local_setup(hass, two_zone_local, setup_risco_local):
    """Test entity setup."""
    registry = er.async_get(hass)
    assert registry.async_is_registered(FIRST_ENTITY_ID)
    assert registry.async_is_registered(SECOND_ENTITY_ID)
    assert registry.async_is_registered(FIRST_ALARMED_ENTITY_ID)
    assert registry.async_is_registered(SECOND_ALARMED_ENTITY_ID)

    registry = dr.async_get(hass)
    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_zone_0_local")})
    assert device is not None
    assert device.manufacturer == "Risco"

    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_zone_1_local")})
    assert device is not None
    assert device.manufacturer == "Risco"


async def _check_local_state(hass, zones, triggered, entity_id, zone_id, callback):
    with patch.object(
        zones[zone_id],
        "triggered",
        new_callable=PropertyMock(return_value=triggered),
    ):
        await callback(zone_id, zones[zone_id])
        await hass.async_block_till_done()

        expected_triggered = STATE_ON if triggered else STATE_OFF
        assert hass.states.get(entity_id).state == expected_triggered
        assert hass.states.get(entity_id).attributes["zone_id"] == zone_id


async def _check_alarmed_local_state(
    hass, zones, alarmed, entity_id, zone_id, callback
):
    with patch.object(
        zones[zone_id],
        "alarmed",
        new_callable=PropertyMock(return_value=alarmed),
    ):
        await callback(zone_id, zones[zone_id])
        await hass.async_block_till_done()

        expected_alarmed = STATE_ON if alarmed else STATE_OFF
        assert hass.states.get(entity_id).state == expected_alarmed
        assert hass.states.get(entity_id).attributes["zone_id"] == zone_id


@pytest.fixture
def _mock_zone_handler():
    with patch("homeassistant.components.risco.RiscoLocal.add_zone_handler") as mock:
        yield mock


async def test_local_states(
    hass, two_zone_local, _mock_zone_handler, setup_risco_local
):
    """Test the various alarm states."""
    callback = _mock_zone_handler.call_args.args[0]

    assert callback is not None

    await _check_local_state(hass, two_zone_local, True, FIRST_ENTITY_ID, 0, callback)
    await _check_local_state(hass, two_zone_local, False, FIRST_ENTITY_ID, 0, callback)
    await _check_local_state(hass, two_zone_local, True, SECOND_ENTITY_ID, 1, callback)
    await _check_local_state(hass, two_zone_local, False, SECOND_ENTITY_ID, 1, callback)


async def test_alarmed_local_states(
    hass, two_zone_local, _mock_zone_handler, setup_risco_local
):
    """Test the various alarm states."""
    callback = _mock_zone_handler.call_args.args[0]

    assert callback is not None

    await _check_alarmed_local_state(
        hass, two_zone_local, True, FIRST_ALARMED_ENTITY_ID, 0, callback
    )
    await _check_alarmed_local_state(
        hass, two_zone_local, False, FIRST_ALARMED_ENTITY_ID, 0, callback
    )
    await _check_alarmed_local_state(
        hass, two_zone_local, True, SECOND_ALARMED_ENTITY_ID, 1, callback
    )
    await _check_alarmed_local_state(
        hass, two_zone_local, False, SECOND_ALARMED_ENTITY_ID, 1, callback
    )
