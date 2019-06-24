# Lutron Caseta Pro Component for Home Assistant

[Lutron](http://www.lutron.com/) is an American lighting control company. They have several lines of home automation devices that manage light switches, dimmers, occupancy sensors, HVAC controls, etc.

This is a custom [Home Assistant](https://home-assistant.io/) component to support the following models of Lutron bridges / main repeaters:

- [Lutron Caseta](http://www.casetawireless.com) Smart Bridge **PRO** (L-BDGPRO2-WH)
- [Ra2 Select](http://www.lutron.com/en-US/Products/Pages/WholeHomeSystems/RA2Select/Overview.aspx) Main Repeater (RR-SEL-REP-BL / RR-SEL-REP2S-BL / RRK-SEL-REP2-BL)

The bridges / main repeaters are supported through their Telnet integration interface which must be enabled for this component to function. The non-PRO model of the Caseta bridge is not supported.

The currently supported Lutron devices are:

- Wall and plug-in dimmers as Home Assistant [lights](https://home-assistant.io/components/light/)
- Wall and plug-in switches as Home Assistant [switches](https://home-assistant.io/components/switch/)
- Scenes as Home Assistant [scenes](https://home-assistant.io/components/scene/)
- Lutron shades as Home Assistant [covers](https://home-assistant.io/components/cover/)
- Pico remotes as Home Assistant [sensors](https://www.home-assistant.io/components/sensor/)
- Fan controllers as Home Assistant [fans](https://www.home-assistant.io/components/fan/)

For first time setup and configuration steps, refer to the [documentation](https://github.com/upsert/lutron-caseta-pro/blob/master/ReadMe.md).