# Lutron Caseta Pro Component for Home Assistant

[Lutron](http://www.lutron.com/) is an American lighting control company. They have several lines of home automation devices that manage light switches, dimmers, occupancy sensors, HVAC controls, etc.

This is a custom [Home Assistant](https://home-assistant.io/) component to support the **PRO** model of the [Lutron Caseta](http://www.casetawireless.com) Smart Bridge and the [Ra2 Select Main Repeater](http://www.lutron.com/en-US/Products/Pages/WholeHomeSystems/RA2Select/Overview.aspx) and their respective product lines. The Smart Bridge PRO (L-BDGPRO2-WH) and Ra2 Select (RR-SEL-REP2-BL) models are supported through their Telnet integration interface. This is only available on the PRO model for Caseta. No other interfaces to the Smart Bridge or Main Repeater are used by this component and the JSON format Integration Report is required to operate.

The currently supported Lutron devices are:

- Wall and plug-in dimmers as Home Assistant [lights](https://home-assistant.io/components/light/)
- Wall and plug-in switches as Home Assistant [switches](https://home-assistant.io/components/switch/)
- Scenes as Home Assistant [scenes](https://home-assistant.io/components/scene/)
- Lutron shades as Home Assistant [covers](https://home-assistant.io/components/cover/)
- Pico remotes as Home Assistant [sensors](https://www.home-assistant.io/components/sensor/)

This component differs from the [Lutron Caseta](https://home-assistant.io/components/lutron_caseta/) component in that it only works with the PRO model and uses the relatively well-documented (although still not officially supported) Telnet interface and the [Lutron Integration Protocol](http://www.lutron.com/TechnicalDocumentLibrary/040249.pdf). The Ra2 Select Main Repeater functions identically to the Caseta PRO model but with support for 100 devices and a different product line of dimmers, switches, fan controls, shades and occupancy sensors that is not compatible with Caseta.

## Custom Component Installation
As this is currently a custom component, it must be installed for it to be loaded by Home Assistant.

1. Create a directory `custom_components` in your Home Assistant configuration directory ('config' share if using [hass.io](https://home-assistant.io/hassio/) with the [Samba](https://home-assistant.io/addons/samba/) add-on or `~/.home-assistant/` for Linux installations).
1. Copy the contents of this project including all sub-directories into the directory `custom_components`.

It should look similar to this after installation:
```
/configuration.yaml
/custom_components/lutron_caseta_pro.py
/custom_components/casetify.py
/custom_components/cover/
/custom_components/light/
 ... etc...
```
3. Edit `configuration.yaml` (see below) and restart Home Assistant.

## Component Setup

1. Enable Telnet Support in the Lutron mobile app under Settings -> Advanced -> Integration. It is also recommended to set a static IP address under Integration -> Network Settings.
1. Enable the component in your Home Assistant `configuration.yaml` using the configuration described below. When the component loads it will look for an Integration Report in the configuration directory of Home Assistant. The file name must be in the format `lutron_caseta_pro_<bridge ip address>.json`, where `<bridge ip address>` is the IP address of the Smart Bridge PRO. If it cannot find the Integration Report, it will use Configurator to prompt the user to enter it on the frontend. This allows the use of copying and pasting on a mobile device between the Lutron mobile app and Home Assistant frontend.

When configured, the `lutron_caseta_pro` component will load the Integration Report and setup **all the zones as dimmable lights unless configured otherwise** (see below).

The name assigned in the Lutron mobile app will be used to form the `entity_id` used in Home Assistant. e.g. a dimmer called 'Ceiling Light' becomes `light.ceiling_light` in Home Assistant. If lights or shades are assigned to an **area** in the Lutron app, the area name will be prepended to the entity_id. e.g. for area 'Dining Room', it would be `light.dining_room_ceiling_light`

## Minimal Configuration

As a minimum, to use Lutron Caseta devices in your installation, add the following to your `configuration.yaml` file using the IP of your Smart Bridge:

```yaml
# Example of minimum configuration.yaml entry
lutron_caseta_pro:
    bridges:
      - host: IP_ADDRESS
```

Configuration variables:

- **bridges** (*Required*): Must be a **list** of smart bridges. Even if you only have one bridge, use `- host` to start the list.
- **host** (*Required*): The IP address of the Lutron Smart Bridge.


## Configuration with Device Types

Additional configuration is provided to set the device types according to the Integration IDs in the JSON integration report:

```yaml
# Example configuration.yaml entry with device types
lutron_caseta_pro:
    bridges:
      - host: IP_ADDRESS
        switch: [ 4, 5 ]
        cover: [ 11, 12 ]
```

Configuration variables:

- **switch** (*Optional*): Array of integration IDs ("ID" in the "Zones" section of integration report)
- **cover** (*Optional*): Array of integration IDs ("ID" in the "Zones" section of integration report)

In the above example Zone 4 and 5 are configured as switches (e.g. `switch.<device name>` in Home Assistant) and zones 11 and 12 are shades (e.g. `cover.<device name>` in Home Assistant). If a listed ID is not found in the Integration Report, it will be ignored.

## Updating
The Integration Report must be updated after any change to device configuration such as pairing new devices or scene renaming. For scenes, only adding or removing a scene or changing a scene's name will modify the Integration Report and changing light or shade levels will not affect it.

To update the custom component, copy the latest files into `custom_components` directory and overwrite existing files. If you have no other custom components, you can remove the contents of the directory before copying the files.

## Pico Remote Sensors
All Pico remotes and wall keypads in the system will each get their own `sensor` in Home Assistant.

The sensor's value will change when a button is pressed according to this [button map](button_map.md).

## Troubleshooting

Enable debugging in your main configuration.yaml to see more logging:

```yaml
logger:
  default: info
  logs:
    custom_components: debug
```

If connection errors are evident, try connecting to the IP listed in the configuration using a Telnet client such as [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html). A connection refused or timeout error indicates the wrong IP address has been used or the Telnet Support has not been enabled in the mobile app under Settings -> Advanced -> Integration.

## TODO

* Confirm compatibility with Lutron occupancy sensors on Ra2 Select.

## Credits

* Based on a [branch](https://github.com/jhanssen/home-assistant/tree/caseta-0.40) of home-assistant authored by [jhanssen](https://github.com/jhanssen/)
