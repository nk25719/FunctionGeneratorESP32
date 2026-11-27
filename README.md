# FunctionGeneratorESP32
This is an ESP32 based two output Function Generator and multi channel oscilloscope.
The ESP32 serves a web page for User Interface.

## Screen shots
| Function Generator Web Page | Oscilloscope Web Page |
| :---: | :---: |
| <img width="500" alt="image" src="https://github.com/user-attachments/assets/19772723-1161-4a72-9972-38874b6fec13" /> | <img width="500" alt="image" src="https://github.com/user-attachments/assets/53694ea1-68ff-4ba8-ba32-0b636ee8b0d0" /><br><br>*Note the Function Generator outputs are looped into the first two inputs.* |


## Fun with Functions.
Using some resistors, the Function Generator, and the oscilloscope we can have some fun with functions.

Lets add two functions through equal resistors (10K) and set the frequencies almost the same.  

<img width="400"   alt="Screenshot 2026-11-12 at 21 43 16" src="https://github.com/user-attachments/assets/79154b6b-fd3f-47ce-8b6a-407f82981681" />  

> Schematic

| Function Generator Web Page | Oscilloscope Web Page |
| :---: | :---: |
| <img width="400"  alt="image" src="https://github.com/user-attachments/assets/a3a3a199-ae50-46a2-a886-85b03ac2377e" />    | <img width="400"  alt="image" src="https://github.com/user-attachments/assets/19f0c000-a51c-4345-8a5f-c8e5cac7c008" />|

Using an external oscilloscope (and adding useing the MATH function) displayingwith a longer time base we get:  
<img width="400" alt="image" src="https://github.com/user-attachments/assets/edec834c-d14d-450c-b38b-d7892bbb8cda" />

> Oscilloscope INSTEK GDS-1054B screen output capture, math function ON

## Folder description 
This repository contains the original standalone waveform sketch and the web-controlled firmware in `firmware/functiongenerator_web/`.

The `feature/multichannel-scope` branch targets the classic ESP32 DevKit (`esp32dev`). It combines two independently controlled DAC outputs with six ADC1 analog scope channels and 17 configurable digital PWM edge-capture inputs. The scope view selects ADC or PWM inputs and overlays selected channels on a full-width graph. The generator remains organized as independent DAC channel cards with one preview per channel. Both DAC outputs start disabled after reboot.

See [`firmware/functiongenerator_web/README.md`](firmware/functiongenerator_web/README.md) for the pin lists, sampling behavior, electrical limits, Wi-Fi setup, and upload instructions. The original `.ino` sketches remain standalone examples.
