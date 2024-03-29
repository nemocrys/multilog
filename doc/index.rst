Welcome to multilog's documentation!
====================================

Measurement data recording and visualization using various devices, e.g.,
multimeters, pyrometers, optical or infrared cameras.

An introduction on how to use multilog can be found on the GitHub page
https://github.com/nemocrys/multilog#multilog.

Program structure
-----------------

multilog follows the model-view-controller pattern. For each measurement
device two classes are defined: a pyQT-QWidget "view" class for
visualization in the *view* module and a "model" class in the *devices*
module. The "controller", including program construction and main
sampling loop, is defined in the *main* module.

Adding a new device
-------------------
To add a new device to, the following steps are required:

- create a device-class implementing the device configuration, sampling, and saving
- create a view-class implementing the GUI
- add the configuration in the *devices* section in the configuration file
- add the new device to the "setup devices & tabs" section (search for "# add new devices here!") in *Controller* class in the *main* module.

External usage
--------------
The device-classes may also be used as a stand-alone interface to the
respective measurement devices in other software. Just copy the required
code from the device module and import it in your python script!


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   devices
   view
   main
   configuration

