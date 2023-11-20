# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 16:49:47 2023

@author: Dimplesx

ABOUT THIS VERSION:
    Script for analysing cells, using data from record tab.
    v02a - added Useable Energy/Power metrics (v02a), cell grouping / some statistics (v02b)
    
"""

### Imports all modules needed
    
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'                     
import numpy as np                        
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import datetime
from tkinter import filedialog
import tkinter as tk
import os

### shortcut to change root name of folder output

root_name = 'Landt_v02a_'

### Script start time

time_start = datetime.datetime.now().replace(microsecond=0)
stamp = time_start.strftime('%Y-%m-%d %Hh%Mm%Ss')
print('Start time = ' + time_start.strftime('%Y-%m-%d %Hh%Mm%Ss'))

### Setting charge and discharge modes

charge = ['CCC', 'CV', 'CCCV']
discharge = ['CCD']

### Defining functions

def browse_button():
    """
    Used in the tk.Button function as the button command. Allows user to select a directory and store it in a global variable (folder_path)
    """
    # Allow user to select a directory and store it in a global variable called folder_path
    global folder_path
    filename = filedialog.askdirectory()
    folder_path.set(filename)
    print('\nInput directory:',filename)
    
def cell_name(file):
    """
    Takes an .xlsx file with the format cell_name_YYMMDD_XXX_Y (where: XXX is battery unit and Y is channel no (1-8)) and reduces it to give just the cell_name
    """
    # Removes .xlsx from end of file name (i.e. cell_name_YYMMDD_XXX_Y, where XXX is battery unit and Y is channel no.)
    file = file.rstrip('.xlsx')
    # Checking for YYMMDD, if present, and removing end of file name up to this point
    if np.char.isnumeric(file[-12:-6]):
        # Removing underscores prior to YYMMDD segment
        if file[-13] == '_':
            if file[-14] == '_':
                return file[:-14]
            else:
                return file[:-13]
        else:
            return file[:-12]
    # Checking for XXX_Y, if present, and removing end of file name up to this point. Also removing underscores prior to XXX_Y segment
    elif file[-6] == '_':
        if file[-7] == '_':
            return file[:-7]
        else:
            return file[:-6]
    # Removing XXX_Y if no underscors prior
    else:
        return file[:-5]
        

def input_yn(prompt = ''):
    """
    Takes a string as a prompt for the user and requires a y/n input. The script only proceeds on a y input
    """
    # Yes / no input prompt
    print(prompt + '\nPlease input one of the following:')
    print("\n 'y'" + "\n 'n'")
    
    while True:
        text = str(input())
        if text == 'y' or text == 'Y':
            break
        elif text == 'n' or text == 'N':
            print("\nPlease complete task and input 'y'")
        else:
            print("\nInvalid input - please input either 'y' or 'n'")
            
def extract_compute(file):
    """
    Takes an .xlsx file and extracts the relevant raw data from it. Uses this data to compute various metrics
    """
    file_name = cell_info_df['FileName'][file]
    cell_name = cell_info_df['CellName'][file]
    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\n\nLoading ' + file_name)
    
    sdf = pd.read_excel(files_folder + '/' + file_name, 'Step-Tab')
    rdf = pd.read_excel(files_folder + '/' + file_name, 'Record-Tab')

    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('\nTime to load ' + file_name + ' = ' + str(t1))

        ### Dropping unuseful columns
        
    sdf.drop('Power/mWh', axis = 1, inplace = True)

    rdf.drop(['TestTime/Sec', 'AuxVolt/V'], axis = 1, inplace = True)
    
        ### Renaming columns
        
    sdf.rename(columns = {'Step':'StepNo'}, inplace = True)        
        
    rdf.rename(columns = {'StepStatus':'Mode'}, inplace = True)
    
        ### Renaming sdfrdf CCVC_C charge mode to match with charge variables list
    
    sdf.replace('CCCV_C', 'CCCV', inplace = True)
    rdf.replace('CCVC_C', 'CCCV', inplace = True)
    
        ### Adding variations of exisiting columns i.e. different time units

    sdf['Period/Min'] = sdf['Period/Sec'] / 60
    sdf['Period/Hr'] = sdf['Period/Sec'] / 3600
    
        ### Adding new columns for names, weights and areas of cells
    
    sdf['FileName'] = file_name
    sdf['CellName'] = cell_name
    
    sdf['FunctionalComponentWeight/g'] = cell_info_df['FunctionalComponentWeight/g'][file]
    sdf['TotalWeight/g'] = cell_info_df['TotalWeight/g'][file]
    sdf['ActiveArea/cm2'] = cell_info_df['ActiveArea/cm2'][file]
    sdf['UseableVoltage/V'] = cell_info_df['UseableVoltage/V'][file]
   
    ### CALCULATING VALUES FROM RAW DATA START HERE

        ### Calculating cycle numbers
    # Start time for entire calculation series
    t = datetime.datetime.now().replace(microsecond=0)
    # Start time for calculation segment
    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\nCalculating cycles for: ' + str(cell_name))

    cycles = []

    for n in range(sdf.shape[0]):
        if len(cycles) == 0:
            cycles.append(1)
        else:
            if sdf['Mode'][n] in discharge:
                cycles.append(cycles[-1])
            elif sdf['Mode'][n] == 'Rest':
                cycles.append(cycles[-1])
            else:
                cycles.append(cycles[-1] + 1)
        

    sdf['CycleNo'] = cycles

    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('Time to calculate cycles = ' + str(t1))

        ### Calculating energy using the sum of Voltage (V) x Current (A) x time (s) for each sub-step in the rdf

    # Substep voltage
    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\nCalculating substep voltages for: ' + str(cell_name))

    substep_voltages = []

    for n in range(rdf.shape[0]):
        if rdf['StepTime/Sec'][n] == 0:
            substep_voltages.append(0)
        elif rdf['StepTime/Sec'][n-1] == 0 and rdf['Mode'][n] in charge:
            substep_voltages.append(rdf['Voltage/V'][n])
        else:
            substep_voltages.append(abs(rdf['Voltage/V'][n] - rdf['Voltage/V'][n-1]))

    rdf['SubstepVoltages/V'] = substep_voltages

    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('Time to calculate substep voltages = ' + str(t1))
    
    # Substep time
    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\nCalculating substep times for: ' + str(cell_name))

    substep_times = []

    for n in range(rdf.shape[0]):
        if rdf['StepTime/Sec'][n] == 0:
            substep_times.append(0)
        else:
            substep_times.append(rdf['StepTime/Sec'][n]-rdf['StepTime/Sec'][n-1])
            
    rdf['SubstepTime/Sec'] = substep_times
    
    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('Time to calculate substep times = ' + str(t1))

    # Substep energy
    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\nCalculating substep energies for: ' + str(cell_name))

    substep_energy = []

    for n in range(rdf.shape[0]):
        if rdf['Mode'][n] in charge:
            substep_energy.append((rdf['Voltage/V'][n] - rdf['SubstepVoltages/V'][n]/2)*rdf['SubstepTime/Sec'][n]*rdf['Current/mA'][n]/1000)
        elif rdf['Mode'][n] == 'Rest':
            substep_energy.append(0)
        else:
            substep_energy.append(abs((rdf['Voltage/V'][n] + rdf['SubstepVoltages/V'][n]/2)*rdf['SubstepTime/Sec'][n]*rdf['Current/mA'][n]/1000))

    rdf['SubstepEnergy/VAs'] = substep_energy
    
    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('Time to calculate substep energies = ' + str(t1))

        ### Summing substep data for each 'StepNo' and merging with step_df
                                
    substep_sum = rdf[['StepNo', 'SubstepEnergy/VAs']].groupby('StepNo').sum().reset_index(drop=False)
    substep_sum = substep_sum.rename(columns={'SubstepEnergy/VAs':'Energy/J'})

    sdf = sdf.merge(substep_sum[['StepNo', 'Energy/J']], how = 'left', on= 'StepNo')

        ### Calculating areal energy from energy (J) and area (cm2) and energy density watt hour (J*3600) and mass (kg)
     
    sdf['ArealEnergy/J/cm2'] = sdf['Energy/J']/sdf['ActiveArea/cm2']
    sdf['FuncEnergyDensity/Wh/kg'] = (sdf['Energy/J']/3600)/(sdf['FunctionalComponentWeight/g']/1000)
    sdf['TotEnergyDensity/Wh/kg'] = (sdf['Energy/J']/3600)/(sdf['TotalWeight/g']/1000)

        ### Calculating energy efficiency
        
    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\nCalculating energy efficiencies for: ' + str(cell_name))

    energy_efficiency = []
        
    for n in range(sdf.shape[0]):
        if sdf['Mode'][n] in charge:
            energy_efficiency.append(0)
        elif sdf['Mode'][n] in discharge and sdf['Mode'][n-1] == 'Rest':
            energy_efficiency.append((sdf['Energy/J'][n]/sdf['Energy/J'][n-2])*100) 
        elif sdf['Mode'][n] == 'Rest':
            energy_efficiency.append(0)     
        else:
            energy_efficiency.append((sdf['Energy/J'][n]/sdf['Energy/J'][n-1])*100)
        
    sdf['EnergyEfficiency/%'] = energy_efficiency

    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('Time to calculate energy efficiencies = ' + str(t1))
       
        ### Calculating charge (C) from capacity (mAh) in sdf

    sdf['Charge/C'] = sdf['Capacity/mAh']*3.6

        ### Calculating coulombic efficiency

    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\nCalculating coulombic efficiencies for: ' + str(cell_name))

    coulombic_efficiency = []

    for n in range(sdf.shape[0]):
        if sdf['Mode'][n] in charge:
            coulombic_efficiency.append(0)
        elif sdf['Mode'][n] in discharge and sdf['Mode'][n-1] == 'Rest':
            coulombic_efficiency.append((sdf['Charge/C'][n]/sdf['Charge/C'][n-2])*100) 
        elif sdf['Mode'][n] == 'Rest':
            coulombic_efficiency.append(0) 
        else:
            coulombic_efficiency.append((sdf['Charge/C'][n]/sdf['Charge/C'][n-1])*100)
        
    sdf['CoulombicEfficiency/%'] = coulombic_efficiency

    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('Time to calculate coulombic efficiencies = ' + str(t1))

        ### Calculating capacitance using charge (C) / Start - End Volt (V).

    sdf['Capacitance/F'] = sdf['Charge/C']/abs(sdf['StartVolt/V'] - sdf['EndVolt/V'])

        ### Calculating areal (cm2) capacitance and capacitance density (g)
        
    sdf['ArealCapacitance/F/cm2'] = sdf['Capacitance/F']/sdf['ActiveArea/cm2']
    sdf['CapacitanceDensity/F/g'] = sdf['Capacitance/F']/sdf['FunctionalComponentWeight/g']

        ### calculating iR drop and resistance, and adding to step_df
    
    t0 = datetime.datetime.now().replace(microsecond=0)
    print('\nCalculating iR drops and resistances for: ' + str(cell_name))    
    
        # Resistance calculated from voltage change (dV/V) / current change (dI/A), between charge and discharge steps. Therefore need final charge current and first discharge current from final and start values for each 'StepNo' in record_df. These are merged onto step_df
    last_condn = rdf['Mode'].isin(charge)
    first_condn = rdf['Mode'].isin(discharge)

    substep_last = rdf[last_condn].groupby('StepNo').last().reset_index(drop=False)
    substep_first = rdf[first_condn].groupby('StepNo').first().reset_index(drop=False)
    
    last_first_comb = pd.concat([substep_last, substep_first]).sort_values('StepNo', ascending = True).reset_index(drop = True)

    sdf = sdf.merge(last_first_comb[['StepNo', 'Current/mA']], how = 'left', on= 'StepNo')
    sdf['Current/mA'] = sdf['Current/mA'].round()
    
    # Calulating iR drop (charge end voltage - discharge start voltage) and resistance values
    sdf['iRDrop/V'] = sdf.loc[0, 'StartVolt/V']
    sdf['Resistance/Ohm'] = 0
    
    for n in range(1, sdf.shape[0]):
        sdf['iRDrop/V'][n] = abs(sdf['EndVolt/V'][n-1] - sdf['StartVolt/V'][n])
        if sdf['Mode'][n] == 'CCD':
            sdf['Resistance/Ohm'][n] = sdf['iRDrop/V'][n] / abs((sdf['Current/mA'][n]-sdf['Current/mA'][n-1])/1000)
        else:
            pass
        
    t1 = datetime.datetime.now().replace(microsecond=0) - t0
    print('Time to calculate iR drops and resistances = ' + str(t1))

        ### Getting systime for the start of each Step segment in rdf and merging it to sdf

    substep_min = rdf.groupby('StepNo').min().reset_index(drop=False)

    sdf = sdf.merge(substep_min[['StepNo', 'SysTime']], how = 'left', on= 'StepNo')

        ### Adding in useable energy / power metrics (v02a) ###
            
    # Checking if useable voltage value has been put in cell_info_df    
    if len(cell_info_df['UseableVoltage/V'].unique()) == 1 and cell_info_df['UseableVoltage/V'].unique()[0] == 0:
        # Reorganising sdf columns
        cols = ['FileName', 'CellName', 'StepNo', 'CycleNo', 'Mode', 'Current/mA', 'Period/Sec',
                'Period/Min', 'Period/Hr',  'Energy/J', 'FuncEnergyDensity/Wh/kg', 'ArealEnergy/J/cm2', 'EnergyEfficiency/%', 'CoulombicEfficiency/%', 'Resistance/Ohm', 'iRDrop/V', 'Capacity/mAh', 'StartVolt/V', 'EndVolt/V', 'Charge/C', 'Capacitance/F', 'ArealCapacitance/F/cm2',
                'CapacitanceDensity/F/g', 'TotEnergyDensity/Wh/kg', 'FunctionalComponentWeight/g', 'TotalWeight/g',
                'ActiveArea/cm2', 'SysTime']
        
        sdf = sdf[cols]
        
    else:
        # Pulling useable substep energy / time from rdf, where condition = voltage + substep voltage (integration value) > useable voltage       
        t0 = datetime.datetime.now().replace(microsecond=0)
        print('\nCalculating useable substep energies and times for: ' + str(cell_name))

        useable_voltage = sdf['UseableVoltage/V'][0]
        useable_substep_energy = []
        useable_substep_time = []

        for n in range(rdf.shape[0]):
            if rdf['Mode'][n] in charge:
                useable_substep_energy.append(0)
                useable_substep_time.append(0)
            elif rdf['Mode'][n] == 'Rest':
                useable_substep_energy.append(0)
                useable_substep_time.append(0)
            elif (rdf['Voltage/V'][n] + rdf['SubstepVoltages/V'][n]/2) < useable_voltage:
                useable_substep_energy.append(0)
                useable_substep_time.append(0)
            else:
                useable_substep_energy.append(rdf['SubstepEnergy/VAs'][n])
                useable_substep_time.append(rdf['SubstepTime/Sec'][n])

        rdf['UseableSubstepEnergy/VAs'] = useable_substep_energy
        rdf['UseableSubstepTime/Sec'] = useable_substep_time
    
        t1 = datetime.datetime.now().replace(microsecond=0) - t0
        print('Time to calculate useable substep energies and times = ' + str(t1))
        
        # Summing useable substep data for each 'StepNo' and merging with step_df                         
        substep_sum = rdf[['StepNo', 'UseableSubstepEnergy/VAs', 'UseableSubstepTime/Sec']] .groupby('StepNo').sum().reset_index(drop=False)
        substep_sum = substep_sum.rename(columns={'UseableSubstepEnergy/VAs':'UseableEnergy/J', 'UseableSubstepTime/Sec':'UseableTime/Sec'})

        sdf = sdf.merge(substep_sum[['StepNo', 'UseableEnergy/J', 'UseableTime/Sec']], how = 'left', on= 'StepNo')
    
        # Calculating useable power
        sdf['UseablePower/W'] = sdf['UseableEnergy/J']/sdf['UseableTime/Sec']
    
        # Calculating useable energy density and useable power density
        sdf['UseableFuncEnergyDensity/Wh/kg'] = (sdf['UseableEnergy/J']/3600)/(sdf['FunctionalComponentWeight/g']/1000)
        sdf['UseableTotEnergyDensity/Wh/kg'] = (sdf['UseableEnergy/J']/3600)/(sdf['TotalWeight/g']/1000)
        sdf['UseableFuncPowerDensity/W/kg'] = sdf['UseablePower/W']/(sdf['FunctionalComponentWeight/g']/1000)
        sdf['UseableTotPowerDensity/W/kg'] = sdf['UseablePower/W']/(sdf['TotalWeight/g']/1000)
    
        # Reorganising sdf columns
        cols = ['FileName', 'CellName', 'StepNo', 'CycleNo', 'Mode', 'Current/mA', 'Period/Sec',
                'Period/Min', 'Period/Hr',  'Energy/J', 'FuncEnergyDensity/Wh/kg', 'ArealEnergy/J/cm2', 'EnergyEfficiency/%', 'CoulombicEfficiency/%', 'Resistance/Ohm', 'iRDrop/V', 'UseableEnergy/J', 'UseableFuncEnergyDensity/Wh/kg','UseablePower/W', 'UseableFuncPowerDensity/W/kg', 'UseableVoltage/V', 'UseableTime/Sec', 'Capacity/mAh', 'StartVolt/V', 'EndVolt/V', 'Charge/C', 'Capacitance/F', 'ArealCapacitance/F/cm2',
                'CapacitanceDensity/F/g', 'TotEnergyDensity/Wh/kg', 'UseableTotEnergyDensity/Wh/kg', 'UseableTotPowerDensity/W/kg', 'FunctionalComponentWeight/g', 'TotalWeight/g',
                'ActiveArea/cm2', 'SysTime']
        
        sdf = sdf[cols]

    ### Total run time for calculation segment
    t1 = datetime.datetime.now().replace(microsecond=0) - t
    print('\nTime to calculate all metrics for ' + cell_name + ' = ' + str(t1))

    ### Return sdf and rdf to global frame
    
    return sdf, rdf


#########     SCRIPT STARTS HERE     #########
    #####  File extract and compute  #####


print('\nPlease navigate to the pop-up box to browse for the folder location in which you have your exported data.' + '\n\nOnce you have selected the folder location please close the pop-up box using the cross in the top right corner.')

### Setting a root file name for the folders and files generated by this script

root_name = root_name

### Opens up a window that will let you select a folder for analysis

root = tk.Tk()
folder_path = tk.StringVar()
BrowseButtonText = 'Click the Browse button below to select the folder with your files.\n\nThe path will appear above this text.\n\nThen close this window with the X button on the top right corner to \ncontinue.'

root.title('Browse')
root.geometry('600x150') 

lbl1 = tk.Label(master=root, textvariable=folder_path)
lbl1.pack()

text_Tk = tk.Text(root, height = 6)
text_Tk.insert(tk.INSERT, BrowseButtonText)
text_Tk.pack()

button2 = tk.Button(master=root, text='Browse', command = browse_button)
button2.pack()
root.mainloop()

files_folder = folder_path.get()

### Creates a folder to house all the outputs of the script 

graphs_folder = files_folder + '\\' + root_name + 'OUT_' + stamp
os.mkdir(graphs_folder)

### Generating cell info .xlsx for each datafile.xlsx in the files_folder location

file_names = []
cell_names = []
group = 1
functional_comp_weight_g = 1
total_weight_g = 1
area_cm2 = 1
useable_voltage = 0     # the cut-off voltage for the cell on discharging

for file in os.listdir(files_folder):
    if file.endswith('xlsx') and not file.startswith('cell_info'):
        file_names.append(file)
        cell_names.append(cell_name(file))

cell_info = {'FileName':file_names, 'CellName':cell_names, 'GroupName':group, 'FunctionalComponentWeight/g':functional_comp_weight_g, 'TotalWeight/g':total_weight_g, 'ActiveArea/cm2':area_cm2, 'UseableVoltage/V':useable_voltage}

cell_info_df = pd.DataFrame.from_dict(cell_info)

cell_info_df.to_excel(files_folder + '\\cell_info_' + stamp + '.xlsx')

### Ask user if they have updated the cell_info .xlsx and closed it. Overwrite old cell_info_df with new .xlsx data 

print('\n' + str(cell_info_df.FileName.count()) + ' files found' + '\\nn')

print(cell_info_df)

input_yn("\n\nHave you updated the cell_info.xlsx and closed it?")

cell_info_df = pd.read_excel(files_folder + '\\cell_info_' + stamp + '.xlsx')

### Extracting raw data from each cell .xlsx file and computing metrics, concatenating the output onto step_df and record_df

# Start time
t0 = datetime.datetime.now().replace(microsecond=0)
print('\n\nCalculating metrics for all cells. Time start = ' + str(t0))

step_df = pd.DataFrame()
step_df.name = 'step_df'
record_df = pd.DataFrame()
record_df.name = 'record_df'

for file in range(cell_info_df.shape[0]):
    sdf, rdf = extract_compute(file)
    
    step_df = pd.concat([step_df, sdf], axis = 0, ignore_index = True)

# Time to calculate metrics for all cells
t1 = datetime.datetime.now().replace(microsecond=0) - t0
print('\n\nTime to calculate metrics for all cells = ' + str(t1))

### Saving step_df and rdf for last cell (currently rdf only for debugging) into the graphs folder

# Saving step_df
t0 = datetime.datetime.now().replace(microsecond=0)
print('\n\nSaving all cell data to ' + graphs_folder)
file_to_save = graphs_folder + '\\cell_data_' + stamp + '.xlsx'
step_df.to_excel(file_to_save)
t1 = datetime.datetime.now().replace(microsecond=0) - t0
print('Time to save step_df = ' + str(t1))

# =============================================================================
# ### Can put this in for debugging rdf calcs ### # Saving rdf of last cell
# t0 = datetime.datetime.now().replace(microsecond=0)
# print('\nSaving rdf of last cell to ' + graphs_folder)
# file_to_save = graphs_folder + '\\rdf_lastcell_' + stamp + '.xlsx'
# rdf.to_excel(file_to_save)
# t1 = datetime.datetime.now().replace(microsecond=0) - t0
# print('Time to save rdf = ' + str(t1))
# =============================================================================



    #####     Generating graphs     #####

    

### Defining function to plot graphs using varying input of X / Y-axis

def plot_graph(data, x, y, title, x_label, y_label):
    """
    data = data, x = x, y = y, legend = 'full', hue = 'CellName', palette = 'nipy_spectral_r'
    
    """
    fig = sns.lineplot(data = data, x = x, y = y, legend = 'full', hue = 'CellName', palette = 'nipy_spectral_r')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(linestyle = 'dashed', linewidth = 0.5)
    sns.move_legend(fig, 'center left', bbox_to_anchor = (1.05, 0.5))
    var = data[y].max() * 1.05
    plt.ylim([0,var])
    
    if x == 'SysTime':
        fig.tick_params(axis = 'x', labelrotation = 60)
        ax = plt.gca()
        dt_fmt = mdates.DateFormatter('%a %d %b, %Hh')
        ax.xaxis.set_major_formatter(dt_fmt)
    
### Separating step_df into charge and discharge dataframes
    
dfc = step_df[step_df['Mode'].isin(charge)]
dfd = step_df[step_df['Mode'].isin(discharge)]

### Creating folders to save graphs into

CycleNo_folder = graphs_folder + '\\CycleNo' 
SysTime_folder = graphs_folder + '\\SysTime'

os.mkdir(CycleNo_folder)
os.mkdir(SysTime_folder) 

### Plotting graphs

# Setting graph paramaters
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['lines.linewidth'] = 1
plt.rcParams['lines.markersize'] = 5
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10 
plt.rcParams['axes.titlepad'] = 12
plt.rcParams['axes.labelpad'] = 4
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['legend.title_fontsize'] = 12
plt.rcParams['figure.figsize'] = [6, 4]

# Graph axes to plot
Xs = ['CycleNo', 'SysTime']   
discharge_y = ['Energy/J', 'FuncEnergyDensity/Wh/kg', 'TotEnergyDensity/Wh/kg', 'ArealEnergy/J/cm2', 'EnergyEfficiency/%', 'CoulombicEfficiency/%', 'Resistance/Ohm', 'iRDrop/V', 'Current/mA', 'UseableEnergy/J', 'UseableFuncEnergyDensity/Wh/kg','UseablePower/W', 'UseableFuncPowerDensity/W/kg',  'UseableTotEnergyDensity/Wh/kg', 'UseableTotPowerDensity/W/kg']
charge_y = ['Energy/J', 'Charge/C', 'EndVolt/V', 'Current/mA']

# Axes labels
labels = {'Energy/J':'Energy [J]', 'FuncEnergyDensity/Wh/kg':'Functional Component\nEnergy Density [Wh/kg]', 'TotEnergyDensity/Wh/kg':'Packet Energy Density\n[Wh/kg]', 'ArealEnergy/J/cm2':'Areal Energy [J/cm^2]', 'EnergyEfficiency/%':'Energy Efficiency [%]', 'CoulombicEfficiency/%':'Coulombic Efficiency [%]', 'Resistance/Ohm':'Resistance [Ohm]', 'iRDrop/V':'iR Drop [V]', 'Charge/C':'Charge [C]', 'CycleNo':'Cycle Number', 'SysTime':'System Time', 'EndVolt/V':'Charge Voltage [V]', 'Current/mA':'Current [mA]','UseableEnergy/J':'Useable Energy [J]', 'UseableFuncEnergyDensity/Wh/kg':'Useable Functonal Comp.\nEnergy Density [ Wh/kg]','UseablePower/W':'Useable Power [W]', 'UseableFuncPowerDensity/W/kg':'Useable Functonal Comp.\nPower Density [ W/kg]',  'UseableTotEnergyDensity/Wh/kg':'Useable Packet Energy\nDensity [Wh/kg]', 'UseableTotPowerDensity/W/kg':'Useable Packet Power\nDensity [W/kg]'}

# File names and paths
file_names = {'Energy/J':'Energy (J)', 'FuncEnergyDensity/Wh/kg':'Func Energy Density (Wh per kg)', 'TotEnergyDensity/Wh/kg':'Packet Energy Density (Wh per kg)', 'ArealEnergy/J/cm2':'Areal Energy (J per cm2)', 'EnergyEfficiency/%':'Energy Efficiency', 'CoulombicEfficiency/%':'Coulombic Efficiency', 'Resistance/Ohm':'Resistance (Ohm)', 'iRDrop/V':'iR Drop (V)', 'Charge/C':'Charge (C)', 'EndVolt/V':'Charge Voltage (V)', 'Current/mA':'Current (mA)','UseableEnergy/J':'Useable Energy (J)', 'UseableFuncEnergyDensity/Wh/kg':'Useable Func E Density (Wh per kg)','UseablePower/W':'Useable Power (W)', 'UseableFuncPowerDensity/W/kg':'Useable Func P Density (W per kg)',  'UseableTotEnergyDensity/Wh/kg':'Useable Packet E Density (Wh per kg)', 'UseableTotPowerDensity/W/kg':'Useable Packet P Density (W per kg)'}

file_paths = {'CycleNo':CycleNo_folder, 'SysTime':SysTime_folder}

# Plotting
specific_metrics = ['FuncEnergyDensity/Wh/kg', 'TotEnergyDensity/Wh/kg', 'ArealEnergy/J/cm2','UseableFuncEnergyDensity/Wh/kg', 'UseableFuncPowerDensity/W/kg', 'UseableTotEnergyDensity/Wh/kg', 'UseableTotPowerDensity/W/kg']
useable_metrics = ['UseableEnergy/J', 'UseableFuncEnergyDensity/Wh/kg','UseablePower/W', 'UseableFuncPowerDensity/W/kg',  'UseableTotEnergyDensity/Wh/kg', 'UseableTotPowerDensity/W/kg']
specific_metric_in_cell_info_df = {'FuncEnergyDensity/Wh/kg':'FunctionalComponentWeight/g', 'UseableFuncEnergyDensity/Wh/kg':'FunctionalComponentWeight/g', 'UseableFuncPowerDensity/W/kg':'FunctionalComponentWeight/g', 'TotEnergyDensity/Wh/kg':'TotalWeight/g', 'UseableTotEnergyDensity/Wh/kg':'TotalWeight/g', 'UseableTotPowerDensity/W/kg':'TotalWeight/g', 'ArealEnergy/J/cm2':'ActiveArea/cm2'}

for x in Xs:
    discharge_path = file_paths[x] + '\\Discharge'
    charge_path = file_paths[x] + '\\Charge'
    os.mkdir(discharge_path)
    os.mkdir(charge_path)
    
    t = datetime.datetime.now().replace(microsecond=0)
    print('\n\nStarting to plot graphs vs ' + x)
    # Discharge
    print('\nPlotting Discharge vs ' + x)
    for y in discharge_y:
        if y in specific_metrics and y in useable_metrics and len(cell_info_df[specific_metric_in_cell_info_df[y]].unique()) == 1 and cell_info_df[specific_metric_in_cell_info_df[y]].unique()[0] == 1 and len(cell_info_df['UseableVoltage/V'].unique()) == 1 and cell_info_df['UseableVoltage/V'].unique()[0] == 0:
            pass 
        elif y in specific_metrics and len(cell_info_df[specific_metric_in_cell_info_df[y]].unique()) == 1 and cell_info_df[specific_metric_in_cell_info_df[y]].unique()[0] == 1:
            pass
        elif y in useable_metrics and len(cell_info_df['UseableVoltage/V'].unique()) == 1 and cell_info_df['UseableVoltage/V'].unique()[0] == 0:
            pass
        else:
            t0 = datetime.datetime.now().replace(microsecond=0)
            plot_graph(data = dfd, x = x, y = y, title = 'Cell Discharge', x_label = labels[x], y_label = labels[y])
            plt.savefig(discharge_path + '\\' + file_names[y] + ' vs ' + x + ' - Discharge.png', bbox_inches='tight')
            plt.show()
            t1 = datetime.datetime.now().replace(microsecond=0) - t0
            print('Plotted ' + y + ' (' + str(t1) + ')')
           
    # Charge
    print('\nPlotting Charge vs ' + x)
    for y in charge_y:
        t0 = datetime.datetime.now().replace(microsecond=0)
        plot_graph(data = dfc, x = x, y = y, title = 'Cell Charge', x_label = labels[x], y_label = labels[y])
        plt.savefig(charge_path + '\\' + file_names[y] + ' vs ' + x + ' - Charge.png', bbox_inches='tight')
        t1 = datetime.datetime.now().replace(microsecond=0) - t0
        plt.show()
        print('Plotted ' + y + ' (' + str(t1) + ')')
   
    t1 = datetime.datetime.now().replace(microsecond=0) - t
    print('\nTime to plot graphs vs ' + x + ' = ' + str(t1))
    
##################################################################################

t1 = datetime.datetime.now().replace(microsecond=0) - time_start
print('\n\nTotal script runtime = ' + str(t1))