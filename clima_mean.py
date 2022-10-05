#!/usr/bin/env python3.7.11
# -*- Coding: UTF-8 -*-

import glob, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def list_files(dir_name):
    '''
    List all files from a directory, sorted by name
    '''
    return sorted(filter(os.path.isfile, glob.glob(dir_name + '/*')))

def empty_df(column_names):
    '''
    Create empty dataframe
    '''
    return pd.DataFrame(columns = column_names)

def read_csv(filename):
    '''
    Read CSV to use like dataframe
    '''
    df = pd.read_csv(filename, encoding='iso-8859-1',\
     decimal=',', delimiter=';', skiprows=8)
    return df

def check_header(df):
    '''
    Check header formats
    '''
    name1 = 'DATA (YYYY-MM-DD)'
    name2 = 'Data'
    colname_hour = 'HORA (UTC)'
    temp_format = 'TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)'
    if name1 in df.columns:
        colname_date = name1
        ts_format = '%Y-%m-%d %H:%M'
    elif name2 in df.columns:
        colname_date = name2
        if 'Hora UTC' in df.columns:
            colname_hour = 'Hora UTC'
        ts_format = '%Y/%m/%d %H%M UTC'
    else:
        print('Cheack header format manually')
        exit()
    return colname_date, colname_hour, ts_format, temp_format

def prepare_df(df, df_all, filename, colname_date, colname_hour,\
 ts_format, temp_format, column_names):
    '''
    Prepare dataframe with all data from multiple CSV files
    '''
    # Create timestamp column
    df['Timestamp'] = df[colname_date] + ' ' + df[colname_hour]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format=ts_format)
    # Select/Rename column
    #print(df.loc[:, df.columns.str.contains('Temp')])
    df.rename(columns = {temp_format:'Temp'}, inplace = True)
    # Get station code in filename and create column with it
    code = filename.split('/')[-1][12:16]
    df['Codigo'] = code
    # Insert in final dataframe
    df_all = df_all.append(df[column_names])
    return df_all

def save_csv(df, filename):
    '''
    Save dataframe to CSV file
    '''
    df.to_csv(filename, index=False)
    return 'CSV saved'

def select_station(df, code):
    '''
    Select rows from same station/code, between two times, between two values;
    Replace invalid values
    '''
    df_station = df.loc[df['Codigo'] == code]
    row_station = [code]
    # Restrict time
    df_station.index = df_station['Timestamp']
    df_station = df_station.between_time('9:00', '21:00')
    # Replace invalid values (-9999) with NaN
    df_station.loc[df_station['Temp'] == -9999, 'Temp'] = np.nan
    # Replace outliers with NaN
    df_station.loc[(df_station['Temp'] < 10) | (df_station['Temp'] > 41), 'Temp'] = np.nan
    return df_station, row_station

def calc_mean(df_station, m):
    '''
    Calculate mean from same month (could be multiple years - climatological mean);
    Insert result in the station line
    '''
    df_month = df_station[df_station['Timestamp'].dt.month == m]
    # Calculate monthly climatological average and insert in the station line
    month_mean = round(df_month['Temp'].mean(),2)
    row_station.append(month_mean)
    return row_station

def loop_month(row_station, df_station, df_means):
    '''
    Loop for months and update dataframe with monthly means
    '''
    for m in range(1,12+1):
        row_station = calc_mean(df_station, m)
    # Insert row with all mean values from station into final DF
    df_means.loc[len(df_means)] = row_station
    return df_means

def plot_ts(df, code):
    '''
    Plot time series
    '''
    filename = f'ts_{code}.png'
    plt.figure(figsize=[14,5])
    plt.title(f'{code}')
    plt.plot(df.index, df['Temp'], linestyle=':', marker='o')
    plt.savefig(filename, bbox_inches='tight')
    plt.close()

################################## MAIN ##################################

list_of_files = list_files('Automaticas_INMET')

# Create empty dataframe with columns to be filled
column_names = ['Codigo', 'Timestamp', 'Temp']
df_all = empty_df(column_names)
for filename in list_of_files:
    # Read CSV file and save in dataframe
    df = read_csv(filename)
    colname_date, colname_hour, ts_format, temp_format = check_header(df)
    df_all = prepare_df(df, df_all, filename, colname_date,\
     colname_hour, ts_format, temp_format, column_names)

# Save all data in final file
#save_csv(df_all, 'all_temp.csv')

# Create empty dataframe with columns to be filled
df_means = empty_df(['Codigo', 'm01', 'm02', 'm03', 'm04',\
 'm05', 'm06', 'm07', 'm08', 'm09', 'm10', 'm11', 'm12'])

# List all stations
codes_lst = list(dict.fromkeys(df['Codigo']))
for code in codes_lst:
    # Create/Prepare dataframe with station data
    df_station, row_station = select_station(df, code)
    # Make a total graph of the station's time series
    plot_ts(df_station, code)
    # Select month and calculate mean
    df_means = loop_month(row_station, df_station, df_means)

# Save data in final file
save_csv(df_means, 'medias_mensais.csv')
