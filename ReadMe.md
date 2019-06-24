# Lutron Caseta Pro Component for Home Assistant

[Lutron](http://www.lutron.com/) is an American lighting control company. They have several lines of home automation devices that manage light switches, dimmers, occupancy sensors, HVAC controls, etc.

This is a custom [Home Assistant](https://home-assistant.io/) component to support the following models of Lutron bridges / main repeaters:

- [Lutron Caseta](http://www.casetawireless.com) Smart Bridge **PRO** (L-BDGPRO2-WH)
- [Ra2 Select](http://www.lutron.com/en-US/Products/Pages/WholeHomeSystems/RA2Select/Overview.aspx) Main Repeater (RR-SEL-REP-BL / RR-SEL-REP2S-BL / RRK-SEL-REP2-BL)

The bridges / main repeaters are supported through their Telnet integration interface which must be enabled for this component to function. The non-PRO model of the Caseta bridge is not supported. No other interfaces to the Smart Bridge or Main Repeater are used by this component.

The currently supported Lutron devices are:

- Wall and plug-in dimmers as Home Assistant [lights](https://home-assistant.io/components/light/)
- Wall and plug-in switches as Home Assistant [switches](https://home-assistant.io/components/switch/)
- Scenes as Home Assistant [scenes](https://home-assistant.io/components/scene/)
- Lutron shades as Home Assistant [covers](https://home-assistant.io/components/cover/)
- Pico remotes as Home Assistant [sensors](https://www.home-assistant.io/components/sensor/)
- Fan controllers as Home Assistant [fans](https://www.home-assistant.io/components/fan/)

This component differs from the [Lutron Caseta](https://home-assistant.io/components/lutron_caseta/) component in that it only works with the PRO model and uses the relatively well-documented (although still not officially supported) Telnet interface and the [Lutron Integration Protocol](http://www.lutron.com/TechnicalDocumentLibrary/040249.pdf).

The Ra2 Select Main Repeater functions identically to the Caseta PRO model but with support for 100 devices and a different product line of dimmers, switches, fan controls, shades and occupancy sensors that is not compatible with Caseta.

## Custom Component Installation
As this is currently a custom component, it must be installed for it to be loaded by Home Assistant.

1. Create a directory `custom_components` in your Home Assistant configuration directory ('config' share if using [hass.io](https://home-assistant.io/hassio/) with the [Samba](https://home-assistant.io/addons/samba/) add-on or `~/.home-assistant/` for Linux installations).
1. Copy `lutron_caseta_pro` from this project including all sub-directories into the directory `custom_components`.

It should look similar to this after installation:
```
/configuration.yaml
/custom_components/lutron_caseta_pro/__init__.py
/custom_components/lutron_caseta_pro/casetify.py
/custom_components/lutron_caseta_pro/cover.py
/custom_components/lutron_caseta_pro/light.py
 ... etc...
```
3. Proceed with first time setup.

## First Time Setup
1. Setup the Lutron app and add all your Lutron devices through the app. Enable Telnet Support under settings menu -> Advanced -> Integration. Also enable static IP under Network Settings and write down the IP.
1. In your Home Assistant installation, install the custom component by copying in the files as noted in the instructions.
1. In Home Assistant `configuration.yaml` create a minimal configuration for the custom component (see below) using the IP address you wrote down and start Home Assistant.
1. Once started and assuming first time setup, open Home Assistant on your mobile device and you should see a notification to Configure Lutron Caseta Smart Bridge PRO on the front-end. Click on Configure and you’ll see a box to paste your Integration Report.
1. Switch over to the Lutron app, go to settings -> Advanced -> Integration -> Send Integration Report. When prompted, select ‘Copy to clipboard’.
1. Switch back to Home Assistant front-end and paste in the Integration Report. If your phone does not have copy and paste options, you will need to share it to yourself through email or to another app that supports copy paste.
1. Once you submit the Integration Report the component should setup all your devices as dimmers and will save the Integration Report to your config directory as a JSON file.
1. If you have switches, fans or Lutron shades, open the Integration Report in your config directory using a text editor and find their Integration IDs and edit your Home Assistant configuration as described in the instructions below to tell it which devices are switches or shades. Unfortunately, the Integration Report does not contain this information so you need to do this manually if you have switches, fans or shades. Restart Home Assistant if you change the yaml file.

After first-time configuration, the JSON-format Integration Report will be saved to your Home Assistant configuration directory as `lutron_caseta_pro_<bridge ip address>.json`, where `<bridge ip address>` is the IP address of the Bridge / Main Repeater. If it cannot find the Integration Report, it will prompt the user to enter it on the frontend.

When configured, the `lutron_caseta_pro` component will load the Integration Report and setup **all the zones as dimmable lights unless configured otherwise** (see below).

The name assigned in the Lutron mobile app will be used to form the `entity_id` used in Home Assistant. e.g. a dimmer called 'Ceiling Light' becomes `light.ceiling_light` in Home Assistant. If lights or shades are assigned to an **area** in the Lutron app, the area name will be prepended to the entity_id. e.g. for area 'Dining Room', it would be `light.dining_room_ceiling_light`

## Minimal Configuration

As a minimum, to use Lutron Caseta devices in your installation, add the following to your `configuration.yaml` file using the IP of your Smart Bridge:

```yaml
# Example of minimum configuration.yaml entry
lutron_caseta_pro:
    bridges:
      - host: IP_ADDRESS
        mac: MAC_ADDRESS
```

Where:
 
- `IP_ADDRESS` is the IP address of your Bridge / Main Repeater (e.g. `192.168.1.100`)

- `MAC_ADDRESS` is the MAC address from the sticker on the bottom
of your Smart Bridge / Main Repeater (e.g. `a0:f6:fd:12:34:56`).

Configuration variables:

- **bridges** (*Required*): Must be a **list** of smart bridges. Even if you only have one bridge, use `- host` to start the list.
- **host** (*Required*): The IP address of the Lutron Smart Bridge / Main Repeater.
- **mac** (*Optional*): The MAC address of the Lutron Smart Bridge / Main Repeater. This is a unique string that is used to
enable the [Entity Registry](https://www.home-assistant.io/docs/configuration/entity-registry/) feature of Home Assistant.
It is optional, but **strongly encouraged** for your configuration to allow for
renaming entities IDs and other customization features in the front-end.


## Configuration

Additional configuration is provided:

```yaml
# Example configuration.yaml entry with device types
lutron_caseta_pro:
    bridges:
      - host: 192.168.1.100
        mac: a0:f6:fd:12:34:56
        default_transition_seconds: 1.0
        # Note: Configure only switches, shades, and fans, all others will be dimmers
        switch: [ 4, 5 ]
        cover: [ 11, 12 ]
        fan: [ 15 ]
```

Configuration variables:

- **default_transition_seconds** (*Optional*): Optional number of seconds to apply to every light transition (both on and off). Only affects dimmable lights and value is in seconds.
- **switch** (*Optional*): Array of integration IDs ("ID" in the "Zones" section of Integration Report)
- **cover** (*Optional*): Array of integration IDs ("ID" in the "Zones" section of Integration Report)
- **fan** (*Optional*): Array of integration IDs ("ID" in the "Zones" section of Integration Report)

In the above example Zone 4 and 5 are configured as switches (e.g. `switch.<device name>` in Home Assistant), Zones 11 and 12 are shades (e.g. `cover.<device name>` in Home Assistant), and Zone 15 is a fan (e.g. `fan.<device name>`). If a listed ID is not found in the Integration Report, it will be ignored.

## Fan Support
When marking a device as a `fan`, the following speeds are available through the `turn_on` or `set_speed` services:
 - `'off'`
 - `'low'`
 - `'medium'`
 - `'medium_high'`
 - `'high'`

If a switch is being used as a fan, call `turn_on` with no `speed` parameter or only use `'off'` or `'high'` for `set_speed`.

## Updating
The Integration Report must be updated after any change to device configuration such as pairing new devices or scene renaming. For scenes, only adding or removing a scene or changing a scene's name will modify the Integration Report and changing light or shade levels will not affect it.

To update the Integration Report, delete the JSON Integration Report from your Home Assistant configuration directory, restart Home Assistant and follow the procedure above for first time setup.

To update the custom component, copy the latest files into `custom_components` directory and overwrite existing files. If you have no other custom components, you can remove the contents of the directory before copying the files.

#### Automatic Updates with HACS (Optional)

For easy updates whenever a new version is released, use the [Home Assistant Community Store](https://github.com/custom-components/hacs) to install the custom component.

HACS will download and install the custom component for you and keep track of updates.

Once HACS is setup, go to Settings -> Custom Repositories and add the following Repository:
``` 
upsert/lutron-caseta-pro
```

And use type `Integration`. Once installed, add your settings to `configuration.yaml` as described above.

## Pico Remote Sensors
All Pico remotes in the system will each get their own `sensor` in Home Assistant.

The sensor's value will change when a button is pressed according to this [button map](button_map.md).

### Example Automation for a Pico Button

```yaml
- alias: Media Pico Button 1
  id: '1522884919017'
  action:
  - alias: Turn on Watch TV
    service: remote.turn_on
    data:
      activity: '29535421'
      entity_id: remote.living_room_harmony
  condition: []
  trigger:
  - platform: state
    entity_id: sensor.media_pico
    to: '1'
```

## Troubleshooting

Enable debugging in your main configuration.yaml to see more logging:

```yaml
logger:
  default: info
  logs:
    custom_components: debug
```

If connection errors are evident, try connecting to the IP listed in the configuration using a Telnet client such as [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html). A connection refused or timeout error indicates the wrong IP address has been used or the Telnet Support has not been enabled in the mobile app under Settings -> Advanced -> Integration.

## Credits

* Based on a [branch](https://github.com/jhanssen/home-assistant/tree/caseta-0.40) of [home-assistant](https://github.com/home-assistant/home-assistant) authored by [jhanssen](https://github.com/jhanssen/)
* Feedback and improvements suggested by the [Home Assistant Community](https://community.home-assistant.io/)
