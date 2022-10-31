devices module
==============
This module contains a class for each device implementing
device configuration, communication and saving of measurement data.

To be compatible with the sampling loop of multilog each device must
implement the following functions:

- init_output(self, directory: str) -> None
- sample(self) -> Any
- save_measurement(self, time_abs: float, time_rel: datetime, sampling: Any) -> None


Daq6510
-------

.. automodule:: multilog.devices.daq6510
   :members:
   :undoc-members:
   :show-inheritance:


IfmFlowmeter
------------

.. automodule:: multilog.devices.ifm_flowmeter
   :members:
   :undoc-members:
   :show-inheritance:


Eurotherm
---------

.. automodule:: multilog.devices.eurotherm
   :members:
   :undoc-members:
   :show-inheritance:


OptrisIP640
-----------

.. automodule:: multilog.devices.optris_ip640
   :members:
   :undoc-members:
   :show-inheritance:



PyrometerLumasense
------------------

.. automodule:: multilog.devices.pyrometer_lumasense
   :members:
   :undoc-members:
   :show-inheritance:



PyrometerArrayLumasense
-----------------------

.. automodule:: multilog.devices.pyrometer_array_lumasense
   :members:
   :undoc-members:
   :show-inheritance:



BaslerCamera
------------

.. automodule:: multilog.devices.basler_camera
   :members:
   :undoc-members:
   :show-inheritance:



ProcessConditionLogger
----------------------

.. automodule:: multilog.devices.process_condition_logger
   :members:
   :undoc-members:
   :show-inheritance:
