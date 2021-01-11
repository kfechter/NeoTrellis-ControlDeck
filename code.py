# Kenneth Fechter 2021
# based on https://learn.adafruit.com/launch-deck-trellis-m4/code-with-circuitpython

import time
import random
import adafruit_trellism4
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode


ROTATION = 0
MEDIA = 1
KEY = 2

keymap = {
 (0,0): (0x001100, MEDIA, ConsumerControlCode.PLAY_PAUSE),
 (0,1): (0x110000, MEDIA, ConsumerControlCode.MUTE),
 (1,0): (0x000033, MEDIA, ConsumerControlCode.VOLUME_INCREMENT),
 (1,1): ((0,0,10), MEDIA, ConsumerControlCode.VOLUME_DECREMENT),

 (0,3): ((0,10,10), KEY, (Keycode.GUI, Keycode.ONE)),
 (1,3): ((0,0,255), KEY, (Keycode.GUI, Keycode.TWO)),
 (2,3): ((0,80,80), KEY, (Keycode.GUI, Keycode.THREE)),
 (3,3): ((255,165,0), KEY, (Keycode.GUI, Keycode.FOUR)),
 (4,3): ((255,255,255), KEY, (Keycode.GUI, Keycode.FIVE)),
 (5,3): ((0,255,255), KEY, (Keycode.GUI, Keycode.SIX)),
 (6,3): ((255,0,0), KEY, (Keycode.GUI, Keycode.SEVEN)),
 (7,3): ((255,0,255), KEY, (Keycode.GUI, Keycode.EIGHT))
}

# Time in seconds to stay lit before sleeping.
TIMEOUT = 90
 
# Time to take fading out all of the keys.
FADE_TIME = 1
 
# Once asleep, how much time to wait between "snores" which fade up and down one button.
SNORE_PAUSE = 0.5
 
# Time in seconds to take fading up the snoring LED.
SNORE_UP = 2
 
# Time in seconds to take fading down the snoring LED.
SNORE_DOWN = 1
 
TOTAL_SNORE = SNORE_PAUSE + SNORE_UP + SNORE_DOWN
 
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)
 
trellis = adafruit_trellism4.TrellisM4Express(rotation=ROTATION)
for button in keymap:
    trellis.pixels[button] = keymap[button][0]
 
current_press = set()
last_press = time.monotonic()
snore_count = -1
while True:
    pressed = set(trellis.pressed_keys)
    now = time.monotonic()
    sleep_time = now - last_press
    sleeping = sleep_time > TIMEOUT
    for down in pressed - current_press:
        if down in keymap and not sleeping:
            print("down", down)
            # Lower the brightness so that we don't draw too much current when we turn all of
            # the LEDs on.
            trellis.pixels.brightness = 0.2
            trellis.pixels.fill(keymap[down][0])
            if keymap[down][1] == KEY:
                kbd.press(*keymap[down][2])
            else:
                cc.send(keymap[down][2])
            # else if the entry starts with 'l' for layout.write
        last_press = now
    for up in current_press - pressed:
        if up in keymap:
            print("up", up)
            if keymap[up][1] == KEY:
                kbd.release(*keymap[up][2])
 
    # Reset the LEDs when there was something previously pressed (current_press) but nothing now
    # (pressed).
    if not pressed and current_press:
        trellis.pixels.brightness = 1
        trellis.pixels.fill((0, 0, 0))
        for button in keymap:
            trellis.pixels[button] = keymap[button][0]
 
    if not sleeping:
        snore_count = -1
    else:
        sleep_time -= TIMEOUT
        # Fade all out
        if sleep_time < FADE_TIME:
            brightness = (1 - sleep_time / FADE_TIME)
        # Snore by pausing and then fading a random button up and back down.
        else:
            sleep_time -= FADE_TIME
            current_snore = int(sleep_time / TOTAL_SNORE)
            # Detect a new snore and pick a new button
            if current_snore > snore_count:
                button = random.choice(list(keymap.keys()))
                trellis.pixels.fill((0, 0, 0))
                trellis.pixels[button] = keymap[button][0]
                snore_count = current_snore
 
            sleep_time = sleep_time % TOTAL_SNORE
            if sleep_time < SNORE_PAUSE:
                brightness = 0
            else:
                sleep_time -= SNORE_PAUSE
                if sleep_time < SNORE_UP:
                    brightness = sleep_time / SNORE_UP
                else:
                    sleep_time -= SNORE_UP
                    brightness = 1 - sleep_time / SNORE_DOWN
        trellis.pixels.brightness = brightness
    current_press = pressed