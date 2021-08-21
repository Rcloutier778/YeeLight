# YeeLight
Client side Yeelight lights controller. The original controller I developed ~2018, now mostly defunct since it just fires off REST calls to YeeLightServer, 
but native functionality can be flipped back on by setting SERVER_ACTS_NOT_CLIENT=False. 

A controller / user interface for the YeeLight smart lights I have around the apartment. Sits in the system tray and has quick select options for pre-determined light modes and 
an advanced mode for in-depth color selection. 

Has hooks for automatically adjusting the lights's color temperature to match 
that of the sun (bright and cold at noon, dim and warm at night). 
