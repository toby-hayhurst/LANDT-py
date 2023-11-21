# LANDT-py
Script used to analyse output data (Excel) of energy storage cells from Landt battery test machines (https://www.landtinst.com/battery-test-systems-for-energy-materials-research/) and provide useful insights with regards to energy storage device performance through data visualisations.

This script works with Landt raw data exported using LANDdt data processing software (https://www.landtinst.com/battery-test-software/) in Excel format. When exporting raw data the following should be confirmed: 

1) Exported cycle range set to suitable value for test data (1-100000).
2) Export file type - Excel
    a) Excel formation - one data file per Excel export file, with each raw data sub-table saving in a single sheet
3) Data items to be included (based on "mA" unit scheme and "Second" as time unit):
    a) Step-Tab Sub-Table:
         i) Step
         ii) Mode
         iii) Period
         iv) Capacity
         v) Power
         vi) Start Volt
         vii) End Volt
    B) Record-Tab Sub-Table:
         i) Test Time
         ii) Step Time
         iii) Current
         iv) Voltage
         v) AuxVolt
         vi) SysTime
         vii) StepNo
         viii) StepStatus
3) Data items to be exncluded:
    a) Cycle-Tab Sub-Table
