"""Support for Etekcity VeSync switches."""
import logging
from homeassistant.core import callback
from homeassistant.components.switch import SwitchDevice
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import VS_DISCOVERY, VS_DISPATCHERS, VS_SWITCHES, DOMAIN
from .common import VeSyncDevice

_LOGGER = logging.getLogger(__name__)

DEV_TYPE_TO_HA = {
    'wifi-switch-1.3': 'outlet',
    'ESW03-USA': 'outlet',
    'ESW01-EU': 'outlet',
    'ESW15-USA': 'outlet',
    'ESWL01': 'switch',
    'ESWL03': 'switch',
    'ESO15-TB': 'outlet'
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up switches."""
    async def async_discover(devices):
        """Add new devices to platform."""
        _async_setup_entities(devices, async_add_entities)

    disp = async_dispatcher_connect(
        hass, VS_DISCOVERY.format(VS_SWITCHES), async_discover)
    hass.data[DOMAIN][VS_DISPATCHERS].append(disp)

    _async_setup_entities(
        hass.data[DOMAIN][VS_SWITCHES],
        async_add_entities
    )
    return True


@callback
def _async_setup_entities(devices, async_add_entities):
    """Check if device is online and add entity."""
    dev_list = []
    for dev in devices:
        if DEV_TYPE_TO_HA.get(dev.device_type) == 'outlet':
            dev_list.append(VeSyncSwitchHA(dev))
        elif DEV_TYPE_TO_HA.get(dev.device_type) == 'switch':
            dev_list.append(VeSyncLightSwitch(dev))
        else:
            _LOGGER.warning("%s - Unkown device type - %s",
                            dev.device_name, dev.device_type)
            continue

    async_add_entities(
        dev_list,
        update_before_add=True
    )


class VeSyncSwitchHA(VeSyncDevice, SwitchDevice):
    """Representation of a VeSync switch."""

    def __init__(self, plug):
        """Initialize the VeSync switch device."""
        super().__init__(plug)
        self.smartplug = plug

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        if hasattr(self.smartplug, 'weekly_energy_total'):
            attr['voltage'] = self.smartplug.voltage
            attr['weekly_energy_total'] = self.smartplug.weekly_energy_total
            attr['monthly_energy_total'] = self.smartplug.monthly_energy_total
            attr['yearly_energy_total'] = self.smartplug.yearly_energy_total
        return attr

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        return self.smartplug.power

    @property
    def today_energy_kwh(self):
        """Return the today total energy usage in kWh."""
        return self.smartplug.energy_today

    def update(self):
        """Update outlet details and energy usage."""
        self.smartplug.update()
        self.smartplug.update_energy()


class VeSyncLightSwitch(VeSyncDevice, SwitchDevice):
    """Handle representation of VeSync Light Switch."""

    def __init__(self, switch):
        """Initialize Light Switch device class."""
        super().__init__(switch)
        self.switch = switch
