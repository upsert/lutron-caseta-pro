# Lutron Caséta PRO Component for Home Assistant

[Lutron](http://www.lutron.com/) is an American lighting control company that produces several popular lines of home automation devices including light switches, dimmers, occupancy sensors, HVAC controls, etc.

This custom [Home Assistant](https://home-assistant.io/) component supports the following Lutron bridges / main repeaters:

- [Lutron Caseta](http://www.casetawireless.com) Smart Bridge **PRO** (*L-BDGPRO2-WH*)
- [RA2 Select](http://www.lutron.com/en-US/Products/Pages/WholeHomeSystems/RA2Select/Overview.aspx) Main Repeater (*RR-SEL-REP-BL / RR-SEL-REP2S-BL / RRK-SEL-REP2-BL*)

These supported bridges and repeaters are integrated using their Telnet interfaces, which **must be enabled** for this component to communicate with the Lutron Caséta devices. For all other Caseta bridges, the [native Home Assistant Lutron Caséta integration](https://www.home-assistant.io/integrations/lutron_caseta/) should be used instead.

Currently supported Lutron devices include:

- Wall and plug-in dimmers as Home Assistant [lights](https://home-assistant.io/components/light/)
- Wall and plug-in switches as Home Assistant [switches](https://home-assistant.io/components/switch/)
- Scenes as Home Assistant [scenes](https://home-assistant.io/components/scene/)
- Lutron shades as Home Assistant [covers](https://home-assistant.io/components/cover/)
- Pico remotes as Home Assistant [sensors](https://www.home-assistant.io/components/sensor/)
- Fan controllers as Home Assistant [fans](https://www.home-assistant.io/components/fan/)

For first time setup and configuration steps, refer to the [documentation](https://github.com/upsert/lutron-caseta-pro/blob/master/README.md).
