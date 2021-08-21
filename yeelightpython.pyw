import yeelight
import time
import yeelight.transitions
import yeelight.enums
import sys
import datetime
import SysTrayIcon as sysTray
import logging
import os
import platform
from tkcolorpicker_custom import colorpicker as clp

from tkinter import *

os.chdir('C:/Users/Richard/Documents/Coding Projects/YeeLight/')

logger = logging.getLogger('log')
logging.basicConfig(filename=os.getcwd() + '/log.log',
                    filemode='a',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S%p',
                    level=logging.INFO)

BULBS = None
SERVER_ACTS_NOT_CLIENT = True
BULB_IPS = ['10.0.0.5', '10.0.0.10', '10.0.0.15', '10.0.0.20']
commands = ['dusk', 'day', 'night', 'sleep', 'off', 'on', 'toggle', 'sunrise', 'autoset', 'logon']
allcommands = commands + ['bright', 'brightness', 'rgb']

__DAY_COLOR = 4000
__DUSK_COLOR = 3300
__NIGHT_COLOR = 2500
__SLEEP_COLOR = 1500

# TODO
"""
1) autoset on wakeup from lan
2) cortana integration
3) hourly light temp color updates
4) Brightness slider in system tray
"""


def main():
    if len(sys.argv) == 1:
        print("No arguments.")
        logger.warning('No arguments.')
        return
    else:
        cmd = sys.argv[1].lower()
        if cmd in allcommands:
            if cmd in commands:
                if cmd != 'autoset':
                    logger.info(cmd)
                globals()[cmd]()
        elif cmd in ['bright', 'brightness']:
            if type(sys.argv[2]) == int:
                print("Changing brightness to %d" % int(sys.argv[2]))
                for i in BULBS:
                    i.set_brightness(int(sys.argv[1]))
        else:
            print("Command \"%s\" not found" % cmd)


def sunrise():
    # Prevent autoset from taking over
    with open(os.getcwd() + '/manualOverride.txt', 'w+') as f:
        f.write(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    overallDuration = 1200000  # 1200000 == 20 min
    on()
    for i in get_bulbs():
        i.set_brightness(0)
        i.set_rgb(255, 0, 0)
    time.sleep(1)
    
    transitions = [yeelight.HSVTransition(hue=39, saturation=100,
                                          duration=overallDuration * 0.5, brightness=80),
                   yeelight.TemperatureTransition(degrees=3200,
                                                  duration=overallDuration * 0.5, brightness=80)]
    
    for i in get_bulbs():
        i.start_flow(yeelight.Flow(count=1, action=yeelight.Flow.actions.stay, transitions=transitions))


def brightness(val):
    # print("Brightness: ",val)
    val = int(val)
    for i in get_bulbs():
        i.set_brightness(val)


def day(duration=3000, auto=False):
    if not auto:
        on()
    # 3200
    colorTempFlow(__DAY_COLOR, duration, 80)


def dusk(duration=3000, auto=False):
    if not auto:
        on()
    # 3000
    colorTempFlow(__DUSK_COLOR, duration, 80)


def night(duration=3000, auto=False):
    if not auto:
        on()
    colorTempFlow(__NIGHT_COLOR, duration, 40)


def sleep(duration=3000, auto=False):
    if not auto:
        on()
    colorTempFlow(__SLEEP_COLOR, duration, 20)

def get_bulbs(timeout=0.2):
    'Get a list of bulbs that are reachable'
    # TODO 
    return BULBS
    bulbs = [yeelight.Bulb(blb['ip']) for blb in yeelight.discover_bulbs(timeout) if blb['ip'] in BULB_IPS]
    if len(bulbs) != len(BULB_IPS):
        logger.info('Found %d bulbs, expected %d', len(bulbs), len(BULB_IPS))
    return bulbs
    
def off():
    bulbs = get_bulbs()
    while True:
        for i in [x for x in bulbs if x.get_properties(['power'])['power'] == 'on']:
            i.turn_off()
        time.sleep(0.2)
        if all(x.get_properties(['power'])['power'] == 'off' for x in bulbs):
            break
    


def on():
    bulbs = get_bulbs()
    while True:
        for i in [x for x in bulbs if x.get_properties(['power'])['power'] == 'off']:
            i.turn_on()
        time.sleep(0.2)
        if all(x.get_properties(['power'])['power'] == 'on' and x.ensure_on() for x in bulbs):
            break
    

def toggle(systray=False):
    """
    Doesn't use the built in toggle command in yeelight as it sometimes fails to toggle one of the lights.
    """
    oldPower = get_bulbs(0.02)[0].get_properties(['power'])['power']
    if oldPower == 'off':
        if systray:
            systrayManualOverride('on')
        if not SERVER_ACTS_NOT_CLIENT:
            on()
    else:
        if systray:
            systrayManualOverride('off')
        if not SERVER_ACTS_NOT_CLIENT:
            off()


def colorTempFlow(temperature=3200, duration=3000, brightness=80):
    # control all lights at once
    # makes things look more condensed
    transition = yeelight.TemperatureTransition(degrees=temperature, duration=duration, brightness=brightness)
    for i in get_bulbs():
        try:
            i.start_flow(yeelight.Flow(count=1,
                                   action=yeelight.Flow.actions.stay,
                                   transitions=[transition]))
        except Exception:
            logger.exception('Failed for %s', str(i))

def logon():
    on()
    autoset(autosetDuration=3000)
    return


def rgbFlow(red=0, green=0, blue=0):
    red = int(red)
    green = int(green)
    blue = int(blue)
    bulbs = get_bulbs()
    bright = bulbs[0].get_properties(['bright'])['bright']
    
    for i in bulbs:
        i.start_flow(yeelight.Flow(count=1, action=yeelight.Flow.actions.stay,
                                   transitions=[yeelight.RGBTransition(red, green, blue, brightness=int(bright))]))


def rgbSet(red=0, green=0, blue=0):
    red = int(red)
    green = int(green)
    blue = int(blue)
    bulbs = get_bulbs()
    bright = bulbs[0].get_properties(['bright'])['bright']
    
    for i in bulbs:
        i.set_rgb(red, green, blue)


def autoset(autosetDuration=300000):
    if all(x.get_properties(['power'])['power'] == 'off' for x in get_bulbs()):
        logger.info('Power is off, cancelling autoset')
        return -1
    # Check if system tray has been used recently to override autoset
    with open(os.getcwd() + '/manualOverride.txt', 'r') as f:
        ld = f.read().strip()
    if datetime.datetime.strptime(ld, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=1) > datetime.datetime.utcnow():
        print("SystemTray used recently, canceling autoset")
        logger.info("SystemTray used recently, canceling autoset")
        return -1
    
    # set light level when computer is woken up, based on time of day
    rn = datetime.datetime.now()  # If there is ever a problem here, just use time.localtime()
    now = datetime.time(rn.hour, rn.minute, 0)
    print('now:', now)
    
    dayrange = ["6:50:AM", "6:00:PM"]
    if time.localtime().tm_wday in [5, 6]:  # weekend
        print("weekend")
        dayrange[0] = "8:30:AM"
    
    # TODO Remember to make changes to raspberry pi too!
    duskrange = [dayrange[1], "7:45:PM"]
    nightrange = [duskrange[1], "9:30:PM"]
    sleeprange = [nightrange[1], "11:00:PM"]
    DNDrange = [sleeprange[1], dayrange[0]]
    
    timeranges = [dayrange, duskrange, nightrange, sleeprange, DNDrange]
    
    for r in timeranges:
        for rr in range(0, 2):
            t = datetime.datetime.strptime(r[rr], "%I:%M:%p")
            r[rr] = datetime.time(t.hour, t.minute, 0)
    
    if dayrange[0] <= now < dayrange[1]:
        print("Day")
        logger.info("Autoset: Day")
        day(autosetDuration, True)
    elif duskrange[0] <= now < duskrange[1]:
        print("Dusk")
        logger.info("Autoset: Dusk")
        dusk(autosetDuration, True)
    elif nightrange[0] <= now < nightrange[1]:
        print("Night")
        logger.info("Autoset: Night")
        night(autosetDuration, True)
    elif sleeprange[0] <= now < sleeprange[1]:
        print("Sleep")
        logger.info("Autoset: Sleep")
        sleep(autosetDuration, True)
    elif DNDrange[0] <= now or now < DNDrange[1]:
        print("dnd")
        logger.info("Autoset: dnd")
        off()
    return 0


def stopMusic():
    bulbs = get_bulbs()
    while any(x.music_mode for x in bulbs):
        for i in bulbs:
            try:
                i.stop_music()
            except Exception:
                pass


if __name__ == "__main__":
    if platform.node() == 'Richard-PC':
        ceiling = yeelight.Bulb("10.0.0.5")
        desk = yeelight.Bulb("10.0.0.10")
        stand = yeelight.Bulb("10.0.0.15")
        stand2 = yeelight.Bulb("10.0.0.20")
        BULBS = [desk, ceiling, stand, stand2]
    else:
        # TODO vlad
        pass

    # If music mode is enabled (Enable it to disable rate limiting)
    stopMusic()
    
    # Run the system tray app
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'systray':
        import glob, itertools, platform, requests
        
        ico = itertools.cycle(glob.glob(os.getcwd() + '/icons/*.ico'))
        
        
        def systrayday(SysTrayIcon):
            logger.info('day')
            if not SERVER_ACTS_NOT_CLIENT:
                day()
            systrayManualOverride('day')
        
        
        def systraydusk(SysTrayIcon):
            logger.info('dusk')
            if not SERVER_ACTS_NOT_CLIENT:
                dusk()
            systrayManualOverride('dusk')
        
        
        def systraynight(SysTrayIcon):
            logger.info('night')
            if not SERVER_ACTS_NOT_CLIENT:
                night()
            systrayManualOverride('night')
        
        
        def systraysleep(SysTrayIcon):
            logger.info('sleep')
            if not SERVER_ACTS_NOT_CLIENT:
                sleep()
            systrayManualOverride('sleep')
        
        
        def systraytoggle(SysTrayIcon):
            logger.info('Toggle')
            toggle(systray=True)
            logger.info('After toggle')
            rn = datetime.datetime.now()
            now = datetime.time(rn.hour, rn.minute, 0)
            # systrayManualOverride() in toggle

        
        
        def systrayManualOverride(newState):
            with open(os.getcwd() + '/manualOverride.txt', 'w+') as f:
                f.write(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            try:
                if platform.node() == 'Richard-PC':
                    systrayUser = 'richard'
                elif platform.node() == 'Vlad':  # TODO
                    systrayUser = 'vlad'
                print(systrayUser)
                data = {"eventType": "manual", "newState": newState}
                print('before post')
                requests.post('http://10.0.0.17:9001', params={}, json=data)
                print('after post')
            except Exception as e:
                logger.error('Failed to post to raspberry pi!')
                print(e)
                pass
        
        
        def systrayColor(SysTrayIcon):
            logger.info('Colors')
            stopMusic()
            initVal = get_bulbs()[0].get_properties(['bright'])['bright']
            initTemp = get_bulbs()[0].get_properties(['ct'])['ct']
            
            for i in get_bulbs():
                i.start_music()
            import ast
            def rgbChanged(*args):
                rgbSet(*ast.literal_eval(__updater.get()))
            
            def brightnessChanged(*args):
                brightness(__brightness.get())
            
            def temperatureChanged(*args):
                print("Temp changed ", __temperature.get())
                for i in get_bulbs():
                    i.set_color_temp(int(__temperature.get()))
            
            def pulseChanged(*args):
                for child in root.winfo_children():
                    child.quit()
                root.quit()
            
            root = Tk()
            root.title('rot')
            root.geometry("0x0-0-0")
            
            __pulse = IntVar(value=0)
            __pulse.trace_variable("w", pulseChanged)
            
            __updater = StringVar()
            __updater.trace_variable("w", rgbChanged)
            
            __brightness = IntVar(value=initVal)
            __brightness.trace_variable('w', brightnessChanged)
            
            __temperature = IntVar(value=initTemp)
            __temperature.trace_variable('w', temperatureChanged)
            
            clp.askcolor(parent=root, yeelight_updater=__updater, pulse=__pulse, bright_updater=__brightness,
                         temp_updater=__temperature)
            try:
                root.destroy()
            except Exception:
                logger.exception('')
            
            stopMusic()
            
            systrayManualOverride('color')
            
            return
        
        
        menu_options = (
            ('Day', next(ico), systrayday),
            ('Dusk', next(ico), systraydusk),
            ('Night', next(ico), systraynight),
            ('Sleep', next(ico), systraysleep),
            ('Custom', next(ico), systrayColor)
        )
        
        sysTray.SysTrayIcon(next(ico), 'Light controller', menu_options, icon_lclick=systraytoggle)
    else:
        # run the python script
        main()