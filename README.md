# Ryzen-5800x3d-linux-undervolting
A Python script to use Ryzen SMU for Linux PBO tuning of Ryzen CPUs. Mostly needed for Ryzen 5800x3d undervolting.
# What is it ?
This is a linux implementation of the PBO2 undevolting tool used to undervolt Ryzen CPUs in Windows. More info on how to do it in Windows is here: https://github.com/PrimeO7/How-to-undervolt-AMD-RYZEN-5800X3D-Guide-with-PBO2-Tuner
# How to use it ?
1. Clone this repository: https://github.com/leogx9r/ryzen_smu and install the Ryzen SMU driver that makes comunication with Ryzen SMU (System Management Unit) possible
```pwsh
git clone https://github.com/leogx9r/ryzen_smu
cd ryzen_smu
make dkms-install
```
Now make areboot. The dkms-install should make a new module into you system called "ryzen_smu". It will autostart next time you reboot your system. Without it the provided Python script will not function.
2. When you have the driver installed and functioning clone this repository and start the undervolting tool.
```pwsh
aaa
```
