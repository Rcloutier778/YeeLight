import yeelight
import time
import yeelight.transitions
import yeelight.enums
import sys
import datetime
import SysTrayIcon as sysTray
import os
import logging
log=logging.getLogger('log')
logging.basicConfig(filename='C:/Users/Richard/Documents/Coding Projects/YeeLight/log.log',
                    filemode='a',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S%p',
                    level=logging.DEBUG)

stand = yeelight.Bulb("10.0.0.5")
desk = yeelight.Bulb("10.0.0.10")
b=[stand,desk]
commands=['dusk','day','night','sleep', 'off', 'on','toggle','sunrise','autoset']
allcommands=commands + ['bright','brightness','rgb']


#TODO
"""
1) autoset on wakeup from lan
2) cortana integration
3) hourly light temp color updates
4) better sunrise transition.
    Currently starts at low red, turns off for whatever reason, then goes from 1500k to 4800k temp color.
    Need to do this in hue/sat or rgb instead I think
5) Brightness slider in system tray
"""

def main():
    #print(desk.get_properties())
    responses=[]
    for i in range(4):
         responses.append(os.system("ping -n 1 10.0.0.7"))
    if 0 not in responses: #timeout, phone not present.
        print("Phone not present.")
        log.warning("Phone not present.")
        off()
        return
    if len(sys.argv) == 1:
        print("No arguments.")
        log.warning('No arguments.')
        return
    else:
        cmd=sys.argv[1].lower()
        if cmd in allcommands:
            if cmd in commands:
                log.info(cmd)
                globals()[cmd]()
        elif cmd in ['bright','brightness']:
            if type(sys.argv[2]) == int:
                print("Changing brightness to %d"%int(sys.argv[2]))
                for i in b:
                    i.set_brightness(int(sys.argv[1]))
        else:
            print("Command \"%s\" not found"%cmd)

def sunrise():
    for i in b:
        i.turn_on()
        i.set_brightness(0)
        i.set_color_temp(0)
    time.sleep(2)
    day(1200000) #1200000 == 20min

def brightness(val):
    for i in b:
        i.set_brightness(val)

def day(duration=3000):
    on()
    colorTempFlow(3200, duration, 80)

def dusk(duration=3000):
    on()
    colorTempFlow(3000, duration, 80)
    
def night(duration=3000):
    on()
    colorTempFlow(2500, duration, 80)

def sleep(duration=3000):
    on()
    colorTempFlow(1500,duration,20)

def off():
    for i in b:
        i.turn_off()

def on():
    for i in b:
        i.turn_on()
        
def toggle():
    for i in b:
        i.toggle()

def colorTempFlow(temperature=3200,duration=3000, brightness=80):
    #control all lights at once
    #makes things look more condensed
    transition=yeelight.TemperatureTransition(degrees=temperature,duration=duration,brightness=brightness)
    for i in b:
        i.start_flow(yeelight.Flow(count=1,
                                   action=yeelight.Flow.actions.stay,
                                   transitions=[transition]))


def lightTime():
    #TODO
    #set light level based on time of day, hour by hour to get smoother transition than day/dusk/night/sleep
    #day=datetime.time.
    #time.time()
    pass

def discoverBulbs():
    bulbs=yeelight.discover_bulbs()
    for bulb in bulbs:
        print(bulb)
    
    
def autoset():
    #set light level when computer is woken up, based on time of day
    rn=datetime.datetime.now() # If there is ever a problem here, just use time.localtime()
    now=datetime.time(rn.hour,rn.minute,0)
    print(now)
    dayrange = ["6:50:AM", "5:00:PM"]
    if time.localtime().tm_wday in [5, 6]: #weekend
        print("weekend")
        dayrange[0] = "8:30:AM"
    duskrange=[dayrange[1],"8:00:PM"]
    nightrange=[duskrange[1],"10:00:PM"]
    sleeprange=[nightrange[1],"11:30:PM"]
    DNDrange=[sleeprange[1],dayrange[0]]
    ranges=[dayrange,duskrange,nightrange,sleeprange,DNDrange]
    for r in ranges:
        for rr in range(0,2):
            t=r[rr].split(":")
            if t[2] == 'PM':
                t[0] = int(t[0]) + 12
            else:
                t[0] = int(t[0])
            t[1]=int(t[1])
            r[rr]=datetime.time(t[0],t[1],0)
            datetime.time()
    for i in ranges:
        print(i)
    print(dayrange[0].strftime("%H:%M:%S"))
    if dayrange[0] <= now < dayrange[1]:
        print("Day")
        day(10000)
    elif duskrange[0] <= now < duskrange[1]:
        print("Dusk")
        dusk(10000)
    elif nightrange[0] <= now < nightrange[1]:
        print("Night")
        night(10000)
    elif sleeprange[0] <= now < sleeprange[1]:
        print("sleep")
        sleep(10000)
    elif DNDrange[0] <= now or now < DNDrange[1]:
        print("dnd")
        off()
        time.sleep(5)
        off()
    return 0

if __name__ == "__main__":
    #Run the system tray app
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'systray':
        import glob, itertools
        ico=itertools.cycle(glob.glob('C:/Users/Richard/Documents/Coding Projects/YeeLight/icons/*.ico'))

        def systrayday(SysTrayIcon):
            day()
        def systraydusk(SysTrayIcon):
            dusk()
        def systraynight(SysTrayIcon):
            night()
        def systraysleep(SysTrayIcon):
            sleep()
        def systraytoggle(SysTrayIcon):
            toggle()
        #TODO on left click, toggle lights
        #TODO brightness slider
        
        menu_options= (('Day', next(ico), systrayday),
                       ('Dusk', next(ico), systraydusk),
                       ('Night', next(ico), systraynight),
                       ('Sleep', next(ico), systraysleep))
        
        sysTray.SysTrayIcon(next(ico),'Light controller',menu_options, icon_lclick=systraytoggle)
    else:
        #run the python script
        main()