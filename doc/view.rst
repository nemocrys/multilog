view module
===========

This module contains the main GUI window and a class for each device
implementing respective the tab.

Each device-widget must implement the following functions to be
compatible with the sampling loop of multilog :

- def set_initialization_data(self, sampling: Any) -> None
- set_measurement_data(self, rel_time: list, meas_data: Any) -> None


MainWindow
----------

.. automodule:: multilog.view.main_window
   :members:
   :undoc-members:
   :show-inheritance:


Base classes
------------

.. automodule:: multilog.view.base_classes
   :members:
   :undoc-members:
   :show-inheritance:


Daq6510Widget
-------------

.. automodule:: multilog.view.daq6510
   :members:
   :undoc-members:
   :show-inheritance:


IfmFlowmeterWidget
------------------

.. automodule:: multilog.view.ifm_flowmeter
   :members:
   :undoc-members:
   :show-inheritance:


EurothermWidget
---------------

.. automodule:: multilog.view.eurotherm
   :members:
   :undoc-members:
   :show-inheritance:


OptrisIP640Widget
-----------------

.. automodule:: multilog.view.optris_ip640
   :members:
   :undoc-members:
   :show-inheritance:



PyrometerLumasenseWidget
------------------------

.. automodule:: multilog.view.pyrometer_lumasense
   :members:
   :undoc-members:
   :show-inheritance:



PyrometerArrayLumasenseWidget
-----------------------------

.. automodule:: multilog.view.pyrometer_array_lumasense
   :members:
   :undoc-members:
   :show-inheritance:



BaslerCameraWidget
------------------

.. automodule:: multilog.view.basler_camera
   :members:
   :undoc-members:
   :show-inheritance:



ProcessConditionLoggerWidget
----------------------------

.. automodule:: multilog.view.process_condition_logger
   :members:
   :undoc-members:
   :show-inheritance:
