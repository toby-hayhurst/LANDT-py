# LANDT-py
This python script takes several output data files (Excel) from Landt battery test machines (https://www.landtinst.com/battery-test-systems-for-energy-materials-research/) and provides useful insights with regards to energy storage device performance for each device, using data visualisations.

This script works with Landt raw data exported using LANDdt data processing software (https://www.landtinst.com/battery-test-software/) in Excel format. When exporting raw data the following should be confirmed:

1) The raw data file should have a file name in the format "name_YYMMDD_XXX_Y", where: "name" is the file name (with no special characters), "YYYMMDD" is the start date of test, "XXX" is the battery unit and "Y" is the channel that the energy storage device was tested on. 
2) Exported cycle range set to suitable value for test data (1-100000).
3) Export file type should be Excel:
    a) Excel formation - one data file per Excel export file, with each raw data sub-table saving in a single sheet
4) Data items to be included (based on "mA" unit scheme and "Second" as time unit):
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
5) Data items to be excluded:
    a) Cycle-Tab Sub-Table
