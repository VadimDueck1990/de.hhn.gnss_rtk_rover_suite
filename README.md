# GNSS Navigation Status

## Overview

### __1. What does this programm do?__

This project was developed in the context of my bachelor's thesis for the Applied Computer Science degree programme at Heilbronn University.

It is a sofware suite consisting of a backend application, which runs on the microcontroller Raspberry Pi Pico W RP2040 and a frontend android application

It is used to perform high precision GNSS measurements using Real-Time-Kinematics(RTK).

The backend project is located in the /de.hhn.gnss_rtk_rover directory.
The frontend project is located in the /de.hhn.gnss_rtk_rover_client_android directory.
In the /Evaluierung directory is the test raw data, which was used in my bachelor thesis.
The firmware and the reset file for Pi Pico W is located in the /pi_pico_w_firmware directory

### __2. Requirements__

To run this programm you'll need at least the following hardware:

Frontend:
* Android Smartphone (Minimum API Level 30: Android 11.0)

Backend:
* Raspberry Pi Pico W RP2040
* SparkFun GPS-RTK2 ZED-F9P GNSS-Receiver


For using the NTRIP Protocol, you need access to a GNSS correction service provider such as SAPOS

## Installation guide (Backend)



### __1. Installing Thonny IDE__
***
On Ubuntu, the first step is to open the terminal and run the following command, for updating the mackage manager
```shell
$ sudo apt update
```
Afterwards you can install thonny with the command
```shell
$ sudo apt install thonny
```
Now you can start Thonny with:
```shell
$ thonny
```

Now the Raspberry Pi Pico W is connected to the computer.

In Thonny, select the Interpreter tab via Run > Configure Interpreter.
In the Interpreter drop-down list, select the MicroPython (Raspberry Pi Pico) option. The port selection can be left as it is so that the Pico is automatically detected. To finish the setup, click OK.

Remark:
On Ubuntu, it may happen that the USB port is not detected and an error in the form of "Could not open serial port /dev/ttyUSB0" is thrown.
This can be fixed by adding the user to the dialout user group as it is missing permissions. The command for this is:
```shell
$ sudo adduser username dialout
```

The Python shell (also called REPL) will now update to show that the Pico W is connected and working. The lower right corner of the Thonny window should now show the interpreter and the USB port to which the Pico W is connected, i.E:
MicroPython (Raspberry Pi Pico) - dev/ttyACM0
For testing you can write a print function that prints "Hello World". If you press Enter, the Pico W should execute the code.

Now the Thonny IDE is ready for MicroPython development. On the left side, two tool windows are displayed. The upper one is a file explorer for the desktop computer and the lower one is the file explorer for the Pico W.


### __2. Flash MicroPython Firmware to the Pi Pico W__
***

The installation of MicroPython is very user-friendly and consists of three main steps:
    1. connect the Pico W as a drive to the desktop computer.
        1. opening a file explorer showing newly connected drives.
        2. connect the Pico W via USB while holding down the BOOTSEL button on the Pico W. 3.
        3. now the Pico W should be listed as RPI-RP2 and contain the files INDEX.HTM and INFO_UF2.TXT.
        4. via the file INDEX.HTM you should now be able to get to the homepage of the Raspberry Foundation.
    2. download MicroPython manually
        1. scroll down the homepage until you see the headings Computers, Accessories and Microcontrollers. The Microcontrollers heading should have a colored underline.
        2. click on MicroPython - Getting started with Micropython.
        3. click on Download the MicroPython UF2 file. This will download the MicroPython firmware for the Pico W. 4.
        4. there are separate download directories for MicroPython for the Raspberry Pi Pico and Pico W: ![Firmware](https://micropython.org/download/rp2-pico-w/)
        There, under Firmware / Releases, download the file marked (latest).
        Note: MicroPython for the Raspberry Pi Pico is board specific. There are different MicroPython versions for the Pico and the Pico W. When saving the firmware, make sure you save the correct version to the board, otherwise important libraries for networking will be missing.
    3. install MicroPython on the Pico W
        1. copy the downloaded .uf2 file to the RPI-RP2 drive.
        2. the file is then copied to the Pico W drive. The drive then logs off and disappears from view.

The MicroPython firmware is automatically installed to the Pico W's internal memory. MicroPython then runs there and remains in memory until the firmware is replaced by another.
The firmware files can also be found in this project repository under /pi_pico_w_firmware.

### __2. Flashing the project to the microcontroller__
***
To install the software on the Pi Pico W you should follow the following steps:
    1. Open up Thonny IDE and make sure, the Pi Pico W is connected and is recognized
    2. Navigate with Thonny's File Explorer for your desktop system to the project folder
    3. Navigate into the backend project /de.hhn.gnns_rtk_rover_suite/de.hhn.gnss_rtk_rover
    4. Before flashing the project, you should set credentials and configurations inside the de.hhn..gnss_rtk_rover/utils/globals.py
       for Wi-Fi, NTRIP and UART connections
            Important: it is recommended to leave the baud rates, as they are set in the project. So it is necessary to change the baud configuration of the ZED-F9P through ![u-blox center](https://www.u-blox.com/en/product/u-center), ![PyGpsClient](https://github.com/semuconsulting/PyGPSClient) or similar program, that can set configurations of u-blox products. Save the configuration to the BBR-Layer, so that it persists between power cycles
    5. Nox you can flash the project to the root-folder of the Pi Pico W
    6. As long as you are in development it is recommended to name the main entry file of the program NOT "main.py". If you use "main.py" the
       micropython interpreter will start the program automatically on boot-up and block any access over USB afterwards. To reset the Pi Pico W you need to connect it in BOOTSEL mode copy the file flash_nuke.uf2 and then the .uf2 Firmware. Both files can be found in this repository under /pi_pico_w_firmware



### __2. Installing Android Application__
***
* To set up the frontend simply install the apk that is found under \bin

### __3. Starting the system__
***
* Configure a Tethering Hotspot on your Android Device, with the credentials, that you set in the backend project in the globals.py file
* Start the rover application from the Thonny IDE or rename the main file to main.py, so that it runs in autonomous mode after the next power
  cycle
* As soon as the builtin LED of the Pi Pico W starts blinking, it means that the microcontroller was able to connect to an Wi-Fi access point
* Now the app is ready to use!
* Alternitavely you can test the rover through the browser. You just need to know his IP. Visit ws://roverip/wstest.html to get live position data on your browser

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments
The Following external Libraries were used in this Project
* [Python GNSS Libraries](https://github.com/semuconsulting) by SEMU Consulting
* [https://github.com/jczic/MicroWebSrv](https://github.com/jczic) by Jean-Christophe Bos

