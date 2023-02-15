import pandas as pd
import numpy as np
import datetime as dt
import os
import holidays
import json
from utils import *

# Load parameters
with open('params.json', 'r') as f_json:
    PARAMS = json.load(f_json)


class Data():
    def __init__(self, path:str=None, f_type:str=None, df:pd.DataFrame=None, name_of_data='', period=None):
        # Create business day offset using holiday calendar for the selected country. Check https://pypi.org/project/holidays/ for supported countries.
        holiday_list = []
        for date, _ in sorted(holidays.country_holidays(PARAMS['country_for_holidays'], years=list(range(1997,2099))).items()):
            holiday_list.append(date)
        self.bday_greece = pd.offsets.CustomBusinessDay(holidays=holiday_list, weekmask= PARAMS['business_days'])
        self.b_hours = pd.offsets.BusinessHour(start=dt.time(PARAMS['business_hours'][0]), end=dt.time(hour = PARAMS['business_hours'][1] -1)) # We need -1 to make it inclusive. So e.g. working hours from 08:00 to 16:00 means that at 16:00 we leave the office.
        self.name = name_of_data
        if period is None:
            self.period = PARAMS['time_resolution'] # H, D, M, Y
        else:
            self.period = period

        if df is not None:
            # This is used in a protected environment (inside program).
            self.data = df

        else:
            if f_type == 'xlsx':

                self.data = pd.read_excel(path)
                if PARAMS['custom_data_load']:
                    self.data = pd.melt(self.data, id_vars = ['Date_'],ignore_index=True, var_name='day_quarter', value_name='Energy').sort_values(['Date_', 'day_quarter'])
                    to_hour_converter = lambda quarter_in_day: (dt.datetime(year = 2020, month=1, day=1, hour=0, minute=0, second=0) + (quarter_in_day -1) * dt.timedelta(days=0, minutes=15)).time()
                    self.data['day_quarter'] = self.data['day_quarter'].apply(to_hour_converter)
                    datetime_as_inserted = pd.to_datetime(self.data.Date_.astype(str) + ' '+ self.data['day_quarter'].astype(str), format='%Y%m%d %H:%M:%S')
                    self.data.insert(0, 'DateTime', datetime_as_inserted)
                    delta = (self.data.iloc[1,0] - self.data.iloc[0,0])
                    hours = delta.seconds//3600
                    minutes = (delta.seconds//60)%60
                    self.data.drop(['Date_', 'day_quarter'], axis=1, inplace=True)
                else:
                    self.data.columns = ['DateTime', 'Energy']
                    self.data.DateTime = pd.to_datetime(self.data.DateTime, infer_datetime_format=True).round('s') # Convert to datetime if not already converted. # If we don't do that (.round('s)), the nano seconds will be non zero.
                delta = (self.data.iloc[1,0] - self.data.iloc[0,0])
                hours = delta.seconds//3600
                minutes = (delta.seconds//60)%60
                if not bool(PARAMS['measurement_is_before_index']): # like not deddie data
                    # Meke them deddie data.
                    self.data.DateTime = self.data.DateTime + pd.Timedelta(hours=hours, minutes=minutes)
                
                self.data.DateTime = self.data.DateTime - pd.Timedelta(hours=hours, minutes=minutes) # shift according to the time interval. That is because the timestamp is after the measurement.

                # We suppose that zero energy is imposible! So we replace every zero with nan
                if not bool(PARAMS['zero_values_are_ok']):
                    self.data['Energy'] = self.data['Energy'].replace(to_replace = 0, value = np.nan)
                if bool(PARAMS['fill_zero_energy_to_previous']): # Fill nan values with linear interpolation.
                    self.data['Energy'] = self.data['Energy'].interpolate()
                    self.data.fillna(method='ffill', inplace=True)
                    self.data.fillna(method='bfill', inplace=True)
                time_resolution = PARAMS['time_resolution'] if period is None else self.period
                if PARAMS['input_type'] == 'power': # Depending on the input type, we do different aggregate operations. This only matters if time interval is not 1 hour (but 15 minutes). Then power != energy consumption in 1 hour.
                    self.data = self.data.resample(time_resolution, on='DateTime', kind = 'timestamp').mean().reset_index() # Sometimes the time interval is in 15 minutes but we convert it to hourly.
                else: # PARAMS['input_type'] == 'energy'
                    self.data = self.data.resample(time_resolution, on='DateTime', kind = 'timestamp').apply(pd.DataFrame.sum,skipna=False).reset_index() # Sometimes the time interval is in 15 minutes but we convert it to hourly.
                if time_resolution == 'H': # We subtract one hour because the first measurement actually concerns the previous day.
                    delta = pd.Timedelta(hours=1, minutes=0)
                elif time_resolution == 'Y' or time_resolution == 'M' or time_resolution == 'W' or time_resolution == 'Q' or time_resolution == 'D': # Then we follow the resolution of the input data and PARAMS['time_resolution'] MUST be equal to that (e.g. 15min)
                    delta = pd.Timedelta(hours=0, minutes=0)
                else: # Then we follow the resolution of the input data and PARAMS['time_resolution'] MUST be equal to that (e.g. 15min)
                    delta = pd.Timedelta(hours=hours, minutes=minutes)
                self.data.index = self.data.DateTime
                if bool(PARAMS['measurement_is_before_index']): # like not deddie data
                    self.data.DateTime = self.data.DateTime + delta # slide back the original array
                self.data.index.name = 'DateTimeStart'
                
            elif f_type == 'csv':
                
                self.data = pd.read_csv(path)
                if PARAMS['custom_data_load']:
                    tmp_data = pd.melt(self.data, id_vars = ['Date_'],ignore_index=True, var_name='day_quarter', value_name='Energy').sort_values(['Date_', 'day_quarter'])
                    to_hour_converter = lambda quarter_in_day: (dt.datetime(year = 2020, month=1, day=1, hour=0, minute=0, second=0) + quarter_in_day * dt.timedelta(days=0, minutes=15)).time()
                    tmp_data['day_quarter'] = tmp_data['day_quarter'].apply(to_hour_converter)
                    datetime_as_inserted = pd.to_datetime(tmp_data.Date_.astype(str) + ' '+ tmp_data['day_quarter'].astype(str), format='%Y%m%d %H:%M:%S')
                    tmp_data.insert(0, 'DateTime', datetime_as_inserted)
                    tmp_data.drop(['Date_', 'day_quarter'], axis=1, inplace=True)
                else:
                    self.data.columns = ['DateTime', 'Energy']
                    self.data.DateTime = pd.to_datetime(self.data.DateTime, infer_datetime_format=True).round('s') # Convert to datetime if not already converted. # If we don't do that (.round('s)), the nano seconds will be non zero.
                delta = (self.data.iloc[1,0] - self.data.iloc[0,0])
                hours = delta.seconds//3600
                minutes = (delta.seconds//60)%60
                if not bool(PARAMS['measurement_is_before_index']): # like not deddie data
                    # Meke them deddie data.
                    self.data.DateTime = self.data.DateTime + pd.Timedelta(hours=hours, minutes=minutes)
                
                
                self.data.DateTime = self.data.DateTime - pd.Timedelta(hours=hours, minutes=minutes) # shift according to the time interval. That is because the timestamp is after the measurement.
                
                # We suppose that zero energy is imposible! So we replace every zero with nan
                if not bool(PARAMS['zero_values_are_ok']):
                    self.data['Energy'].replace(to_replace = 0, value = pd.NA, inplace=True)
                if bool(PARAMS['fill_zero_energy_to_previous']): # Fill nan values with linear interpolation.
                    self.data['Energy'] = self.data['Energy'].interpolate()
                    self.data.fillna(method='ffill', inplace=True)
                
                time_resolution = PARAMS['time_resolution'] if period is None else self.period
                if PARAMS['input_type'] == 'power': # Depending on the input type, we do different aggregate operations. This only matters if time interval is not 1 hour (but 15 minutes). Then power != energy consumption in 1 hour.
                    self.data = self.data.resample(time_resolution, on='DateTime', kind = 'timestamp').mean().reset_index() # Sometimes the time interval is in 15 minutes but we convert it to hourly.
                else: # PARAMS['input_type'] == 'energy'
                    self.data = self.data.resample(time_resolution, on='DateTime', kind = 'timestamp').sum().reset_index() # Sometimes the time interval is in 15 minutes but we convert it to hourly.
                if time_resolution == 'H':
                    delta = pd.Timedelta(hours=1, minutes=0)
                elif time_resolution == 'Y' or time_resolution == 'M' or time_resolution == 'W' or time_resolution == 'Q' or time_resolution == 'D': # Then we follow the resolution of the input data and PARAMS['time_resolution'] MUST be equal to that (e.g. 15min)
                    delta = pd.Timedelta(hours=0, minutes=0)
                else: # Then we follow the resolution of the input data and PARAMS['time_resolution'] MUST be equal to that (e.g. 15min)
                    delta = pd.Timedelta(hours=hours, minutes=minutes)
                self.data.index = self.data.DateTime
                if bool(PARAMS['measurement_is_before_index']): # like not deddie data
                    self.data.DateTime = self.data.DateTime + delta # slide back the original array
                self.data.index.name = 'DateTimeStart'
            else:
                raise NotImplementedError
            
        
        # print(f"\nData loaded with name: {os.path.split(path)[-1].rsplit('.',maxsplit=1)[0]}\n")
    def get_time_delta(self):
        delta = (self.data.iloc[1,0] - self.data.iloc[0,0])
        return delta
    def get_data_head(self, num_rows=5):
        return self.data.head(num_rows)

    def resample(self, period):
        new_data = self.data.copy()

        delta = (self.data.iloc[1,0] - self.data.iloc[0,0])
        hours = delta.seconds//3600
        minutes = (delta.seconds//60)%60
        new_data.DateTime = new_data.DateTime - pd.Timedelta(hours=hours, minutes=minutes) # shift according to the time interval. That is because the timestamp is after the measurement.

        
        if PARAMS['input_type'] == 'power': # Depending on the input type, we do different aggregate operations. This only matters if time interval is not 1 hour (but 15 minutes). Then power != energy consumption in 1 hour.
            new_data = new_data.resample(period, on='DateTime', kind = 'timestamp').mean().reset_index() # Sometimes the time interval is in 15 minutes but we convert it to hourly.
        else: # PARAMS['input_type'] == 'energy'
            new_data = new_data.resample(period, on='DateTime', kind = 'timestamp').apply(pd.DataFrame.sum,skipna=False).reset_index() # Sometimes the time interval is in 15 minutes but we convert it to hourly.
        if period == 'H': # We subtract one hour because the first measurement actually concerns the previous day.
            delta = pd.Timedelta(hours=1, minutes=0)
        elif period == 'Y' or period == 'M' or period == 'W' or period == 'Q' or period == 'D': # Then we follow the resolution of the input data and PARAMS['time_resolution'] MUST be equal to that (e.g. 15min)
            delta = pd.Timedelta(hours=0, minutes=0)
        else: # period is minutes
            delta = pd.Timedelta(hours=hours, minutes=minutes)

        new_data.index = new_data.DateTime
        new_data.DateTime = new_data.DateTime + delta # slide back the original array
        new_data.index.name = 'DateTimeStart'
        
        return new_data
    
    @classmethod
    def concatenate(cls,d1,d2):
        return pd.concat([d1.data,d2.data])

    @classmethod
    def group(cls,d_list):
        data_frame_list =  map(lambda x: x.data, d_list)
        data_frame_list_ready_for_concatenation = map(lambda x: x.drop(columns = ['DateTime']), data_frame_list)
        merged = pd.concat(data_frame_list_ready_for_concatenation, axis=1, join='inner').sum(axis=1).to_frame()
        merged.columns = ['Energy']
        merged.insert(loc=0, column='DateTime', value = merged.index + pd.Timedelta(hours=1)) # Add DateTime Column.
        if merged.empty:
            return None
        
        return merged

    def get_keys(self):
        # returns the unique keys in an array form.
        if type(self.data.index) is pd.MultiIndex:
            return (self.data.index.get_level_values(0).unique(), self.data.index.get_level_values(1).unique()), True
        else:
            return (self.data.index.get_level_values(0).unique(), []), False
        
    def select(self, values):
        # values in the case of multi-index should be a tuple of two arrays. In the case of singel index, it should be a tuple with one array inside.
        # returns a dataframe of the same type as the input.
        if type(self.data.index) is pd.MultiIndex:
            vals = pd.MultiIndex.from_product(values)
            good_keys = self.data.index.intersection(vals)
            return self.data.loc[good_keys, :]
        else:
            # print("hi there")
            #print(values[0])
            good_keys = self.data.index.intersection(values[0])
            # print(good_keys)
            return self.data.loc[good_keys, :]
            

class energy_stats_data(Data):
    def __init__(self, period, path=None, f_type=None, df=None, name=''):
        super().__init__(path, f_type, df,name)
        assert period is not None
        self.period = period

    @classmethod
    def compare(cls, d1, d2, outer_join, compare_period_aligned):
        data_are_same = False if d1 is not d2 else True
        assert d1.period == d2.period # Periods must be equal for comparison to be made!
        d1data = d1.data.copy()
        d2data = d2.data.copy()
        if d1.period == 'D' or d1.period == 'H':
            # Append name of dataset on the 1st level of columns.
            d1data.columns = d1data.columns.set_levels([d1data.columns.levels[0][0] +'_1_'+d1.name],level=0)
            d2data.columns = d2data.columns.set_levels([d2data.columns.levels[0][0] +'_2_'+d2.name],level=0)
            if not outer_join: # inner join
                # if data_are_same:
                    # if data are the same, then there is no point in doing inner join but anyway.
                if not compare_period_aligned:
                    res = d1data.merge(d2data,left_index=True, right_index=True, how='inner',indicator=True, suffixes=('x','y'))
                else:
                    # Needed to verify cross product and for the anti - merge.
                    d1data.insert(0, 'idx_copy_1', d1data.index)
                    d2data.insert(0, 'idx_copy_2', d2data.index)
                    
                    res = d1data.merge(d2data, how='cross')
                    res.index = pd.MultiIndex.from_product([d1data.index,d2data.index], names=['DateTimeStart_1_', 'DateTimeStart_2_'])
                    res = res[res['idx_copy_1']!=res['idx_copy_2']]
                    if d1.period == 'H':
                        res = res[res['idx_copy_1'].hour == res['idx_copy_2'].hour] # Filter out common values in indexes.
                    elif d1.period == 'D':
                        res = res[res['idx_copy_1'].day == res['idx_copy_2'].day]
                    else:
                        raise ValueError("Invalid period! How did you get here?")
                    d1data.drop(['idx_copy_1'], axis=1, inplace=True)
                    d2data.drop(['idx_copy_2'], axis=1, inplace=True)
                    res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)
            else:
                # Needed to verify cross product and for the anti - merge.
                d1data.insert(0, 'idx_copy_1', d1data.index)
                d2data.insert(0, 'idx_copy_2', d2data.index)
                
                res = d1data.merge(d2data, how='cross')
                res.index = pd.MultiIndex.from_product([d1data.index,d2data.index], names=['DateTimeStart_1_'+d1.name, 'DateTimeStart_2_'+d2.name])
                if data_are_same:
                    res = res[res['idx_copy_1']!=res['idx_copy_2']].copy() # Filter out common values in indexes.
                d1data.drop(['idx_copy_1'], axis=1, inplace=True)
                d2data.drop(['idx_copy_2'], axis=1, inplace=True)
                res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)

            res.insert(0, 'percent_difference_mean_power', (res[(res.columns.levels[0][0],'mean')] - res[(res.columns.levels[0][1],'mean')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][1],'mean')]) * 100)
            res.insert(0, 'first_data_mean_minus_second_data_mean', res[(res.columns.levels[0][0],'mean')] - res[(res.columns.levels[0][1],'mean')])
            res.insert(0, 'percent_difference_sum_energy_consumption', (res[(res.columns.levels[0][0],'sum')] - res[(res.columns.levels[0][1],'sum')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][1],'sum')]) * 100)
            res.insert(0, 'first_data_sum_minus_second_data_sum', res[(res.columns.levels[0][0],'sum')] - res[(res.columns.levels[0][1],'sum')])
        
        elif d1.period == 'W' or d1.period == 'M':
            # Append name of dataset on the 1st level of columns.
            d1data.columns = d1data.columns.set_levels([d1data.columns.levels[0][0] +'_1_'+d1.name, d1data.columns.levels[0][1] +'_1_'+d1.name],level=0)
            d2data.columns = d2data.columns.set_levels([d2data.columns.levels[0][0] +'_2_'+d2.name,d1data.columns.levels[0][1] +'_2_'+d2.name ],level=0)

            if not outer_join: # inner join
                if not compare_period_aligned:
                    res = d1data.merge(d2data,left_index=True, right_index=True, how='inner',indicator=True, suffixes=('x','y'))
                else:
                    # Needed to verify cross product and for the anti - merge.
                    d1data.insert(0, 'idx_copy_1', d1data.index)
                    d2data.insert(0, 'idx_copy_2', d2data.index)
                    
                    res = d1data.merge(d2data, how='cross')
                    res.index = pd.MultiIndex.from_product([d1data.index,d2data.index], names=['DateTimeStart_1_', 'DateTimeStart_2_'])
                    res = res[res['idx_copy_1']!=res['idx_copy_2']]
                    if d1.period == 'W':
                        res = res[pd.Int64Index(res['idx_copy_1'].isocalendar().week) == pd.Int64Index(res['idx_copy_2'].isocalendar().week)] # Filter out common values in indexes.
                    elif d1.period == 'M':
                        res = res[res['idx_copy_1'].month == res['idx_copy_2'].month]
                    else:
                        raise ValueError("Invalid period! How did you get here?")
                    d1data.drop(['idx_copy_1'], axis=1, inplace=True)
                    d2data.drop(['idx_copy_2'], axis=1, inplace=True)
                    res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)
            else:
                # Needed to verify cross product and for the anti - merge.
                d1data.insert(0, 'idx_copy_1', d1data.index)
                d2data.insert(0, 'idx_copy_2', d2data.index)
                
                res = d1data.merge(d2data, how='cross')
                res.index = pd.MultiIndex.from_product([d1data.index,d2data.index], names=['DateTimeStart_1_'+d1.name, 'DateTimeStart_2_'+d2.name])
                if data_are_same:
                    res = res[res['idx_copy_1']!=res['idx_copy_2']].copy() # Filter out common values in indexes.
                d1data.drop(['idx_copy_1'], axis=1, inplace=True)
                d2data.drop(['idx_copy_2'], axis=1, inplace=True)
                res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)

            res.insert(0, 'percent_difference_mean_daily', (res[(res.columns.levels[0][0],'mean')] - res[(res.columns.levels[0][1],'mean')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][1],'mean')])* 100)
            res.insert(0, 'first_data_daily_mean_consumption_minus_second_data_mean_daily_consumption', res[(res.columns.levels[0][0],'mean')] - res[(res.columns.levels[0][1],'mean')])
            res.insert(0, 'percent_difference_hourly_mean_power', (res[(res.columns.levels[0][2],'mean')] - res[(res.columns.levels[0][3],'mean')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][3],'mean')])* 100)
            res.insert(0, 'first_data_hourly_mean_minus_second_data_hourly_mean', res[(res.columns.levels[0][2],'mean')] - res[(res.columns.levels[0][3],'mean')])
            res.insert(0, 'percent_difference_monthly_sum_energy_consumption', (res[(res.columns.levels[0][2],'sum')] - res[(res.columns.levels[0][3],'sum')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][3],'sum')])* 100)
            res.insert(0, 'first_data_monthly_sum_minus_second_data_monthly_sum', res[(res.columns.levels[0][2],'sum')] - res[(res.columns.levels[0][3],'sum')])
        
        elif d1.period == 'Y' or d1.period == 'Q':
            # Append name of dataset on the 1st level of columns.
            d1data.columns = d1data.columns.set_levels([d1data.columns.levels[0][0] +'_1_'+d1.name, d1data.columns.levels[0][1] +'_1_'+d1.name, d1data.columns.levels[0][2] +'_1_'+d1.name],level=0)
            d2data.columns = d2data.columns.set_levels([d2data.columns.levels[0][0] +'_2_'+d2.name, d2data.columns.levels[0][1] +'_2_'+d2.name, d2data.columns.levels[0][2] +'_2_'+d2.name],level=0)

            if not outer_join: # inner join
                if not compare_period_aligned:
                    res = d1data.merge(d2data,left_index=True, right_index=True, how='inner',indicator=True, suffixes=('x','y'))
                else:
                    # Needed to verify cross product and for the anti - merge.
                    d1data.insert(0, 'idx_copy_1', d1data.index)
                    d2data.insert(0, 'idx_copy_2', d2data.index)
                    
                    res = d1data.merge(d2data, how='cross')
                    res.index = pd.MultiIndex.from_product([d1data.index,d2data.index], names=['DateTimeStart_1_', 'DateTimeStart_2_'])
                    res = res[res['idx_copy_1']!=res['idx_copy_2']]
                    if d1.period == 'Y':
                        res = res[res['idx_copy_1'].year == res['idx_copy_2'].year] # Filter out common values in indexes.
                    elif d1.period == 'Q':
                        res = res[res['idx_copy_1'].quarter == res['idx_copy_2'].quarter]
                    else:
                        raise ValueError("Invalid period! How did you get here?")
                    d1data.drop(['idx_copy_1'], axis=1, inplace=True)
                    d2data.drop(['idx_copy_2'], axis=1, inplace=True)
                    res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)
            else:
                # Needed to verify cross product and for the anti - merge.
                d1data.insert(0, 'idx_copy_1', d1data.index)
                d2data.insert(0, 'idx_copy_2', d2data.index)
                
                res = d1data.merge(d2data, how='cross')
                res.index = pd.MultiIndex.from_product([d1data.index,d2data.index], names=['DateTimeStart_1_'+d1.name, 'DateTimeStart_2_'+d2.name])
                if data_are_same:
                    res = res[res['idx_copy_1']!=res['idx_copy_2']].copy() # Filter out common values in indexes.
                d1data.drop(['idx_copy_1'], axis=1, inplace=True)
                d2data.drop(['idx_copy_2'], axis=1, inplace=True)
                res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)

            res.insert(0, 'percent_difference_mean_monthly', 100 *(res[(res.columns.levels[0][0],'mean')] - res[(res.columns.levels[0][1],'mean')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][1],'mean')]))
            res.insert(0, 'first_data_monthly_mean_consumption_minus_second_data_mean_monthly_consumption', res[(res.columns.levels[0][0],'mean')] - res[(res.columns.levels[0][1],'mean')])

            res.insert(0, 'percent_difference_mean_daily', 100 *(res[(res.columns.levels[0][2],'mean')] - res[(res.columns.levels[0][3],'mean')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][2],'mean')]))
            res.insert(0, 'first_data_daily_mean_consumption_minus_second_data_mean_daily_consumption', res[(res.columns.levels[0][2],'mean')] - res[(res.columns.levels[0][3],'mean')])
            res.insert(0, 'percent_difference_hourly_mean_power', 100 * (res[(res.columns.levels[0][4],'mean')] - res[(res.columns.levels[0][5],'mean')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][4],'mean')]))
            res.insert(0, 'first_data_hourly_mean_minus_second_data_hourly_mean', res[(res.columns.levels[0][4],'mean')] - res[(res.columns.levels[0][5],'mean')])
            res.insert(0, 'percent_difference_sum_energy_consumption', 100 *(res[(res.columns.levels[0][4],'sum')] - res[(res.columns.levels[0][5],'sum')]) / (np.finfo(np.float64).eps * 10 + res[(res.columns.levels[0][4],'sum')]))
            res.insert(0, 'first_data_sum_minus_second_data_sum', res[(res.columns.levels[0][4],'sum')] - res[(res.columns.levels[0][5],'sum')])

        else:
            raise ValueError('No other period is supported!')
        return res


class energy_distribution(Data):
    def __init__(self, period, path=None, f_type=None, df=None, name=''):
        super().__init__(path, f_type, df,name)
        assert period is not None
        self.period = period

    @classmethod
    def compare(cls, d1):
        
        d1data = d1.data.copy()
        d2data = d1.data.copy()

        # Append name of dataset on the 1st level of columns.
        d1data.columns = d1data.columns.set_levels([x +'_1'  for x in d1data.columns.levels[0]],level=0)
        d2data.columns = d2data.columns.set_levels([x +'_2'  for x in d2data.columns.levels[0]],level=0)

        # Needed to verify cross product and for the anti - merge.
        d1data.insert(0, 'idx_copy_1', d1data.index)
        d2data.insert(0, 'idx_copy_2', d2data.index)
        
        res = d1data.merge(d2data, how='cross')
        res.index = pd.MultiIndex.from_product([d1data.index,d2data.index], names=['DateTimeStart_1', 'DateTimeStart_2'])
        
        res = res[res['idx_copy_1']!=res['idx_copy_2']].copy() # Filter out common values in indexes.
        d1data.drop(['idx_copy_1'], axis=1, inplace=True)
        d2data.drop(['idx_copy_2'], axis=1, inplace=True)
        res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)

        list_to_loop_over1 = list(d1data.columns.get_level_values(0).unique())
        list_to_loop_over1.reverse()

        list_to_loop_over2 = list(d2data.columns.get_level_values(0).unique())
        list_to_loop_over2.reverse()

        for load1, load2 in zip(list_to_loop_over1, list_to_loop_over2):
            
            res.insert(0, 'percent_difference_mean_power_'+ load1 + '_and_' + load2, (res[(load1,'mean')] - res[(load2,'mean')]) / 100*(np.finfo(np.float64).eps * 10 + res[(load1,'mean')]))
            res.insert(0, 'first_data_mean_minus_second_data_mean_'+ load1 + '_and_' + load2, res[(load1,'mean')] - res[(load2,'mean')])
            res.insert(0, 'percent_difference_sum_energy_'+ load1 + '_and_' + load2, (res[(load1,'sum')] - res[(load2,'sum')]) / 100*(np.finfo(np.float64).eps * 10 + res[(load1,'sum')]))
            res.insert(0, 'first_data_sum_minus_second_data_sum_'+ load1 + '_and_' + load2, res[(load1,'sum')] - res[(load2,'sum')])
        
        return res

class energy_stats_comparison(Data):
    def __init__(self, period, path=None, f_type=None, df=None, name=''):
        super().__init__(path, f_type, df,name)
        assert period is not None
        self.period = period

class typical_day_comparison(Data):
    def __init__(self, period, path=None, f_type=None, df=None, name=''):
        super().__init__(path, f_type, df,name)
        assert period is not None
        self.period = period
    

class energy_distribution_comparison(Data):
    def __init__(self, period, path=None, f_type=None, df=None, name=''):
        super().__init__(path, f_type, df,name)
        assert period is not None
        self.period = period

class typical_day(Data):
    def __init__(self, period, path=None, f_type=None, df=None, name=''):
        super().__init__(path, f_type, df,name)
        assert period is not None
        self.period = period

    @classmethod
    def compare(cls, d1):
        # There is no point in comparing when d1.period is no period.
        period = d1.period
        if period == 'no_period':
            return None

        d1data = d1.data.copy()
        d2data = d1.data.copy()

        # Append name of dataset on the 1st level of columns.
        d1data.columns = d1data.columns.set_levels([x +'_1'  for x in d1data.columns.levels[0]],level=0)
        d2data.columns = d2data.columns.set_levels([x +'_2'  for x in d2data.columns.levels[0]],level=0)

        # Needed to ensure that we do not compare two same rows.
        d1data.insert(0, 'idx_copy_1', d1data.index)
        d2data.insert(0, 'idx_copy_2', d2data.index)

        # Tricky thing to preform later cross product on a 3-level indexed array. We actually move all indexes (e.g. month, year, quarter) to columns and leve as the only index the hour (yes index is not unique but hey it's pandas so we can do that).
        d1data  = d1data.reset_index(level=list(range(len(d1data.index.levels)-1)))
        d2data  = d2data.reset_index(level=list(range(len(d2data.index.levels)-1)))
        
        # Time for the join.
        res = d1data.merge(d2data, how='inner', left_on=['hour'], right_on=['hour'])
        res['hour'] = res.index.get_level_values(0)
        res = res[res['idx_copy_1']!=res['idx_copy_2']].copy() # Filter out common values in indexes.
        d1data.drop(['idx_copy_1'], axis=1, inplace=True)
        d2data.drop(['idx_copy_2'], axis=1, inplace=True)
        res.drop(['idx_copy_1','idx_copy_2'], axis=1, inplace=True)

        # Add required statistics (the whole point was that).
        res.insert(0, 'percentage(x-y)/x', (res[('Energy_1', 'mean')] - res[('Energy_2', 'mean')]) / (100*(np.finfo(np.float64).eps * 10 + res[('Energy_1', 'mean')])    ) )
        res.insert(0, 'mean_energy_difference(x-y)', res[('Energy_1', 'mean')] - res[('Energy_2', 'mean')])

        # Sort values.
        if period == 'Q': 
            res_sorted = res.sort_values(['year_x', 'quarter_x','year_y', 'quarter_y'])
            arr1 = pd.to_datetime(res_sorted.year_x.astype(str) + '-'+ res_sorted.quarter_x.astype(str) + ' '+ res_sorted.index.get_level_values(0).astype(str), format='%Y-%m %H')
            arr2 = pd.to_datetime(res_sorted.year_y.astype(str) + '-'+ res_sorted.quarter_y.astype(str) + ' '+ res_sorted.index.get_level_values(0).astype(str), format='%Y-%m %H')
        elif period == 'M': 
            res_sorted = res.sort_values(['year_x', 'month_x','year_y', 'month_y'])
            arr1 = pd.to_datetime(res_sorted.year_x.astype(str) + '-'+ res_sorted.month_x.astype(str) + ' '+ res_sorted.index.get_level_values(0).astype(str), format='%Y-%m %H')
            arr2 = pd.to_datetime(res_sorted.year_y.astype(str) + '-'+ res_sorted.month_y.astype(str) + ' '+ res_sorted.index.get_level_values(0).astype(str), format='%Y-%m %H')
        elif period == 'W': 
            res_sorted = res.sort_values(['year_x', 'month_x', 'week_x', 'year_y', 'month_y','week_y'])
            # it will not be datetime if week is provided.
            arr1 = res_sorted.year_x.astype(str) + '--'+ res_sorted.month_x.astype(str) + '--'+ res_sorted.week_x.astype(str) + '--'+ res_sorted.index.get_level_values(0).astype(str)
            arr2 = res_sorted.year_y.astype(str) + '--'+ res_sorted.month_y.astype(str) + '--'+  res_sorted.month_y.astype(str) + '--'+  res_sorted.index.get_level_values(0).astype(str)
        else:
            raise ValueError("Period not supported!")
        
        res_sorted.index = pd.MultiIndex.from_arrays([arr1, arr2])
        res_sorted.index.names = ['index x', 'index y']
        return res_sorted

class energy_data(Data):
    def __init__(self, path=None, f_type=None, df=None, name='', period=None):
        super().__init__(path, f_type, df, name, period = period)
        self.filtered_data = energy_data.filter_rows(self.data)
        self.min_day, self.max_day = self.get_min_max()

    def get_min_max(self):
        # We need to add timedelta +1 hour becouse when creating the index, we subtracted one hour.
        return ((self.data.index.min() + pd.Timedelta(hours=1)).date(), self.data.index.max().date())

    @classmethod
    def to_hourly_rows(cls, data_pd:pd.DataFrame, type_data=PARAMS['input_type']):
        hourly_data = data_pd
        delta = (hourly_data.iloc[1,0] - hourly_data.iloc[0,0])
        hours = delta.seconds//3600
        if hours < 0: # If the data resolution is less than hourly
            if type_data == 'power':
                hourly_data = hourly_data.resample('H', kind = 'timestamp').agg({'DateTime': 'last', 'Energy': 'mean'})
            elif type_data == 'energy':
                hourly_data = hourly_data.resample('H', kind = 'timestamp').agg({'DateTime': 'last', 'Energy': 'sum'})
            else:
                raise ValueError('Not supported input type (in json parameter file)!')
        return hourly_data

    @classmethod
    def filter_rows(cls, data_pd:pd.DataFrame, dropnan_v = True, drop_zeros=bool(PARAMS['drop_zero_energy'])):

        filtered = data_pd
        if dropnan_v:
            filtered = filtered.dropna()
        if drop_zeros:
            filtered = filtered[filtered['Energy'] !=0]
        return filtered

    def select_rows(self, time_interval:tuple[dt.date, dt.date]=None, bdays=0, bhours=0, filtered=True) -> pd.DataFrame:
        
        # Time interval staff.
        s_y, s_m, s_d = time_interval[0].year, time_interval[0].month, time_interval[0].day
        e_y, e_m, e_d = time_interval[1].year, time_interval[1].month, time_interval[1].day
        # Be cautious: If inclusive is set to left (below) then you need to advance the end date by 1 day (not included in date range).
        # data_view = self.data.loc[pd.date_range( start=time_interval[0], end=time_interval[1]+dt.timedelta(1) , freq='H', inclusive='left')] 
        
        if filtered:
            local_data = self.filtered_data
        else:
            local_data = self.data
        
        mask = (local_data['DateTime'] >= dt.datetime(s_y, s_m, s_d, 1, 0, 0)) & (local_data['DateTime'] <= (dt.datetime(e_y, e_m, e_d, 0, 0, 0) + dt.timedelta(days=1))) # We need that + 1 because 23:00 - 00:00 energy's data are saved on next day.
        data_view = local_data.loc[mask] # select rows in the specified interval.
        
        # Filter for business days
        if bdays == 1:
            # Filter by index and keep only the dates that are business days.
            data_view = data_view[data_view.index.map(self.bday_greece.is_on_offset)]
        if bdays == 2:
            # Filter by index and keep only the dates that are not business days.
            data_view = data_view[~data_view.index.map(self.bday_greece.is_on_offset)]

        # Filter for hours
        if bhours == 1:
            # Filter by index and keep only the dates that are business days.
            data_view = data_view[data_view.index.map(self.b_hours.is_on_offset)]
        if bhours == 2:
            # Filter by index and keep only the dates that are not business days.
            data_view = data_view[~data_view.index.map(self.b_hours.is_on_offset)]
        print(data_view)
        return data_view

    @classmethod
    def get_energy_distribution(cls, energy_data_list, period:str='M', time_interval:tuple[dt.date,dt.date]=None, b_d=0, b_h=0, first_data_object_is_total_energy=False) ->pd.DataFrame:
        # Filter the energy data in the input list.
        for d in energy_data_list:
            try:
                assert d.period == energy_data_list[0].period # assert that they have same periods.
            except AssertionError as err:
                print(err)
                raise err
        
        name_list = [d.name for d in energy_data_list] # Get names of data objects
        if time_interval is None:
            data_view_list = [energy_data.to_hourly_rows(d.filtered_datad).drop(columns = ['DateTime'], errors='ignore') for d in energy_data_list]
        else:
            data_view_list = [energy_data.to_hourly_rows(d.select_rows(time_interval, b_d, b_h, filtered=True)).drop(columns = ['DateTime'], errors='ignore') for d in energy_data_list]
    
        if bool(PARAMS['same_count']):
            for dat in data_view_list:
                if dat.empty:
                    print("One of the resulted dataframes is empty!")
                    return None
            data_distribution = pd.concat(data_view_list, axis=1, join='inner',keys=name_list) # inner join to keep same kees in case we have different indexes.
            print(data_distribution)
            data_distribution = data_distribution.groupby(data_distribution.index.to_period(period)).agg(['sum', 'mean', 'count'])
        else:
            # If we don't care wether we have the same support (count) when computing energy.
            results_list = []
            for d in data_view_list:
                # Group every dataframe in list to period.
                results_list.append(d['Energy'].groupby(d.index.to_period(period)).agg(['sum', 'mean', 'count']))
            print("Lista onomatwn:", name_list)
            data_distribution = pd.concat(results_list, axis=1, join='inner')
        print(data_distribution)
        iterables = [name_list, ["sum", "mean", "count"]]
        data_distribution.columns = pd.MultiIndex.from_product(iterables)

        # If total energy is provided, add some columns (percentage of total and other loads)
        if first_data_object_is_total_energy:
            sums = data_distribution.loc[:, (data_distribution.columns.get_level_values(0), ['sum'])]
            means = data_distribution.loc[:, (data_distribution.columns.get_level_values(0), ['mean'])]

            num_of_sub_columns = data_distribution.columns.get_level_values(1).unique().to_list().__len__() + 1
            for i,key in enumerate(data_distribution.columns.get_level_values(0).unique().to_list(), start=1): # or just in name_list
                val = data_distribution[(key, 'sum')] / data_distribution[data_distribution.columns[0]] * 100
                data_distribution.insert(i * num_of_sub_columns -1 , column = (key, 'percentage'), value=val)
            name_list.append('other_loads')

            data_distribution[('other_loads', 'sum')] = (2*sums.iloc[:,0]) - sums.sum(axis='columns')
            data_distribution[('other_loads', 'mean')] = (2*means.iloc[:,0]) - means.sum(axis='columns')
            data_distribution[('other_loads', 'percentage')] = data_distribution[('other_loads', 'sum')] / data_distribution[data_distribution.columns[0]] * 100
            
        return data_distribution
        
    def get_typical_day(self,time_interval:tuple[dt.date, dt.date]=None, b_d:int=0, b_h:int=0, period:str='M', reference_day=None) -> pd.DataFrame:
        
        if period == 'H':
            print("No support for hourly period in this operation!")
            return None
        if period == 'D':
            print("No point in daily period. The typical day can not be computed in a daily period!")
            return None

        data_view = self.filtered_data if time_interval is None else self.select_rows(time_interval, b_d, b_h, filtered=True)

        # Convert to hourly delta interval if period is not hourly. This is because periods like week and month will sum the sub-energies of <1h intervals, so total consumption will be way higher (if 'power' is provided, if 'energy' is provided we will be ok for the sum column but not ok for the 'mean' column as it will not show the power).
        data_view = energy_data.to_hourly_rows(data_view)

        # Another filter: the computations will include only days which have measurements for all the 24 hours of a day.
        x = data_view.resample('D').asfreq()[data_view.resample('D').count() == 24].dropna()
        df1 = pd.DataFrame({
            "Energy": 1.0,
            "DateTime":[x.index[-1]]
        }, index=[x.index[-1]+ dt.timedelta(days=1)])
        x =pd.concat([x,df1])
        ok_values_tmp = data_view.index.intersection(x.resample('H',closed='left').ffill(limit=23).dropna()[:-1].index)
        data_view_new = data_view.loc[ok_values_tmp]

        # Calculate the typical day for the given period.
        if period == 'Q': # mean hour for all the days in a quarter (in a year of course(?)).
            tmp_res = data_view_new.groupby([ data_view_new.index.year, data_view_new.index.quarter, data_view_new.index.hour], as_index=True).agg({'Energy':['mean', 'min', 'idxmin', 'max', 'idxmax']})
            tmp_res.index.names = ['year', 'quarter', 'hour']
        elif period == 'M': # mean hour for all the days in a month (of a certain year).
            tmp_res = data_view_new.groupby([ data_view_new.index.year, data_view_new.index.month, data_view_new.index.hour], as_index=True).agg({'Energy':['mean', 'min', 'idxmin', 'max', 'idxmax']})
            tmp_res.index.names = ['year', 'month', 'hour']
        elif period == 'no_period': # mean hour for all the days in a month (of a certain year).
            tmp_res = data_view_new.groupby([data_view_new.index.hour], as_index=True).agg({'Energy':['mean', 'min', 'idxmin', 'max', 'idxmax']})
            tmp_res.index.names = ['hour']
        elif period == 'W': # mean hour for all the days in a week (of a certain year).
            tmp_res = data_view_new.groupby([data_view_new.index.year, data_view_new.index.month, data_view_new.index.week, data_view_new.index.hour], as_index=True).agg({'Energy':['mean', 'min', 'idxmin', 'max', 'idxmax']})
            tmp_res.index.names = ['year', 'month', 'week', 'hour']
        else:
            raise ValueError("Period not supported!")


        # # In order to compute min and max day, we have first to take the mean power of each day (so as to see which is the minimum/maximum and find their indices).
        # tmp_res_min_max = data_view_new.groupby(data_view_new.index.to_period('D')).sum(numeric_only=True)

        # # min/max day in which period ? This is what we will do now. We will find one min/max for each period.
        # if period != 'no_period':
        #     # Find min max according to given period.
        #     tmp_res_min_max_days = tmp_res_min_max.resample(period).agg(['idxmin', 'idxmax', 'min', 'max'])
        #     # Resample to hourly. Befor it was with <period> time interval.
        #     tmp_res_min_max_days_hourly = tmp_res_min_max_days.resample('H', convention='start').ffill().to_timestamp()
        #     # After resampling, we may added some indexes that are not in the original, tmp_res dataframe. So need to filter those out.
        #     ok_values = tmp_res_min_max_days_hourly.index.intersection(data_view_new.index)
        #     tmp_res_min_max_days_hourly_filtered = tmp_res_min_max_days_hourly.loc[ok_values,:]
        #     # Use the indexes for each period to find the energy values of the day with the least consumption.
        #     tmp_data_min_per_month = data_view_new[data_view_new.index.to_period(freq='D') == tmp_res_min_max_days_hourly_filtered[('Energy', 'idxmin')]]
        #     # Do the same to find the energy values of the day with the most consumption.
        #     tmp_data_max_per_month = data_view_new[data_view_new.index.to_period(freq='D') == tmp_res_min_max_days_hourly_filtered[('Energy', 'idxmax')]]

        #     if period == 'Q': # mean hour for all the days in a quarter (in a year of course(?)).
        #         tmp_data_min_per_month_to_append = tmp_data_min_per_month.groupby([ tmp_data_min_per_month.index.year, tmp_data_min_per_month.index.quarter, tmp_data_min_per_month.index.hour], as_index=True).agg({'Energy':['min']}) # Fake aggregation. Actually it is the identity function.
        #         tmp_data_max_per_month_to_append = tmp_data_max_per_month.groupby([ tmp_data_max_per_month.index.year, tmp_data_max_per_month.index.quarter, tmp_data_max_per_month.index.hour], as_index=True).agg({'Energy':['max']}) # Fake aggregation. Actually it is the identity function.
                
        #     elif period == 'M': # mean hour for all the days in a month (of a certain year).
        #         tmp_data_min_per_month_to_append = tmp_data_min_per_month.groupby([ tmp_data_min_per_month.index.year, tmp_data_min_per_month.index.month, tmp_data_min_per_month.index.hour], as_index=True).agg({'Energy':['min']}) # Fake aggregation. Actually it is the identity function.
        #         tmp_data_max_per_month_to_append = tmp_data_max_per_month.groupby([ tmp_data_max_per_month.index.year, tmp_data_max_per_month.index.month, tmp_data_max_per_month.index.hour], as_index=True).agg({'Energy':['max']}) # Fake aggregation. Actually it is the identity function.
                
        #     elif period == 'no_period': # mean hour for all the days in a month (of a certain year).
        #         # There is no such case here.
        #         pass
        #     elif period == 'W': # mean hour for all the days in a week (of a certain year).
        #         tmp_data_min_per_month_to_append = tmp_data_min_per_month.groupby([ tmp_data_min_per_month.index.year, tmp_data_min_per_month.index.week, tmp_data_min_per_month.index.hour], as_index=True).agg({'Energy':['min']}) # Fake aggregation. Actually it is the identity function.
        #         tmp_data_max_per_month_to_append = tmp_data_max_per_month.groupby([ tmp_data_max_per_month.index.year, tmp_data_max_per_month.index.week, tmp_data_max_per_month.index.hour], as_index=True).agg({'Energy':['max']}) # Fake aggregation. Actually it is the identity function.
                
        #     else:
        #         raise ValueError("Period not supported!")
            
        #     # Append those values to the tmp_res dataframe.
        #     tmp_res[('Energy', 'min_day')] = tmp_data_min_per_month_to_append
        #     tmp_res[('Energy', 'max_day')] = tmp_data_max_per_month_to_append

        # else:
        #     min_idx = tmp_res_min_max.idxmin()
        #     max_idx = tmp_res_min_max.idxmax()
        #     tmp_res[('Energy', 'min_day')] = data_view_new.loc[data_view_new.index.to_period(freq='D') == min_idx[0]].groupby([data_view_new.index.hour], as_index=True).agg({'Energy':['min']})
        #     tmp_res[('Energy', 'max_day')] = data_view_new.loc[data_view_new.index.to_period(freq='D') == max_idx[0]].groupby([data_view_new.index.hour], as_index=True).agg({'Energy':['max']})

        # And we finished!
        return tmp_res

        

    def get_energy_stats(self, period:str='M', time_interval:tuple[dt.date, dt.date]=None, b_d=0, b_h=0) -> pd.DataFrame:

        data_view = self.filtered_data if time_interval is None else self.select_rows(time_interval, b_d, b_h, filtered=True)
        if period != 'H':
            # Convert to hourly delta interval if period is not hourly. This is because periods like week and month will sum the sub-energies of <1h intervals, so total consumption will be way higher (if 'power' is provided, if 'energy' is provided we will be ok for the sum column but not ok for the 'mean' column as it will not show the power).
            data_view = energy_data.to_hourly_rows(data_view)
        # Add average daily consumption for one [day, week, month, year]
        data_stats_without_daily_statistics = data_view.groupby(data_view.index.to_period(period)).agg({'Energy':['sum','mean', 'min', 'idxmin', 'max', 'idxmax', 'std', 'count']})
        data_stats_without_daily_statistics.columns = data_stats_without_daily_statistics.columns.map(lambda x: (get_daily_monthly_etc(period)+'_Energy_Hourly_Stats', x[1]))
        if period == 'H':
            # For the next operations, convert the data to hourly, if not alredy in hourly. Again, for the same reason as above.
            data_view = energy_data.to_hourly_rows(data_view)

        # Compute daily statistics.
        hours_in_day = data_view.groupby(data_view.index.to_period('D')).count()[['Energy']].max()[0]
        dily_statistics_tmp = data_view.groupby(data_view.index.to_period('D')).mean(numeric_only=True) * hours_in_day # Compute daily consumption (of course, filters on working hours may still apply). We need resample instead of groupby(to period) because we need the datetime properties of the index so as to perform another group by.
        dily_statistics_tmp = dily_statistics_tmp.to_timestamp()
        dily_statistics = dily_statistics_tmp.groupby(dily_statistics_tmp.index.to_period(period)).agg({'Energy':['mean', 'min', 'idxmin', 'max', 'idxmax', 'std', 'count']}) # Compute daily statistics on daily power consumption. No need to sum because we have already computed that. Then group by the chosen period for the indexes of the 2 dataframes to match.
        # Add multi-index columns to the new dataframe.
        iterables = [["Daily_Energy"], ["mean", "min", 'idxmin', "max", 'idxmax', "std", "count"]]
        dily_statistics.columns = pd.MultiIndex.from_product(iterables)

        # Compute monthly statistics.
        monthly_statistics_tmp = data_view.groupby(data_view.index.to_period('M')).sum(numeric_only=True) # Compute monthly consumption (of course, filters on working hours and days may still apply). We need resample instead of groupby(to period) because we need the datetime properties of the index so as to perform another group by.
        monthly_statistics_tmp = monthly_statistics_tmp.to_timestamp()
        monthly_statistics = monthly_statistics_tmp.groupby(monthly_statistics_tmp.index.to_period(period)).agg({'Energy':['mean', 'min', 'idxmin', 'max','idxmax', 'std', 'count']}) # Compute monthly statistics on monthly power consumption. No need to sum because we have already computed that. Then group by the chosen period for the indexes of the 2 dataframes to match.
        # Add multi-index columns to the new dataframe.
        iterables_Month = [["Monthly_Energy"], ["mean", "min","idxmin", "max", "idxmax", "std", "count"]]
        monthly_statistics.columns = pd.MultiIndex.from_product(iterables_Month)

        if period == 'D' or period == 'H':# Period is Daily, then no point in calculating daily and monthly statistics.
            data_total = data_stats_without_daily_statistics

        elif period == 'Y' or period == 'Q': # Only on these cases there is a point in calculating  monthly statistics (i.e. statistics regarding the power consumption of the month).
            data_total = pd.concat([data_stats_without_daily_statistics, dily_statistics,monthly_statistics], axis=1, join='inner')
        else: # 
            
            data_total =  pd.concat([data_stats_without_daily_statistics, dily_statistics], axis=1, join='inner') # Concatenate on the columns level.
        
        return data_total
            
        
    