main module
===========

This module brings together the model and view of the devices. It
implements the construction of the GUI and controls the sampling.

To ensure continuous sampling, each device is run in a separate QThread.
Communication with the main thread is implemented using pyqtSignals that
trigger the data acquisition / GUI update.


.. automodule:: multilog.main
   :members:
   :undoc-members:



