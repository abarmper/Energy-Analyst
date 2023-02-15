from data_analysis import *
from tqdm import tqdm
import re
from utils import *

class Functionality():
    def __init__(self):
        self.energy_data_dict = {}
        self.saver = results() # Initialise saver class.
        self.state = state_saver() # Initialise state saver class (create folders etc.).
        self.time_interval_dict_memory_start = dict() # start_date
        self.time_interval_dict_memory_end = dict() # end_date
        self.buffer = None # Used to remember the last output in case user wants to save it. (dataframe, name, class_type, period)
        self.gen = generaor_for_unamed_dataframes()

    def load_data_from_fn_paths(self,fn_tuple, period):
        file_name_and_path_and_type = []
        for f_path in fn_tuple:
            # Get name of file from path & remove extention.
            file_name = os.path.split(f_path)[-1]
            # Get the name that will be used as key. We don't want any white space nor any trailing space.
            data_name = file_name.rsplit('.',maxsplit=1)[0].strip() # Strip of any whitespace left or right.
            data_name = re.sub('\s+', '_', data_name) # Replace inner white spaces with _ .
            if period is not None and period != PARAMS['time_resolution']:
                data_name = data_name + '_period_' + period
            f_type = file_name.rsplit('.',maxsplit=1)[-1] 
            file_name_and_path_and_type.append((data_name, f_path, f_type))
        
        for data_name, f_path, file_type in tqdm(file_name_and_path_and_type):
            # Create energy data object (loads data).
            ed1 = energy_data(f_path, f_type=file_type, name=data_name, period=period)
        
            # Add data object to the dictionary of data objects for future use.
            self.energy_data_dict[data_name] = ed1

    def load_latest_state(self, name=None):
            if name is None:
                self.energy_data_dict = self.state.load_latest_state()
                if self.energy_data_dict == dict():
                    print('Problem loading state!')
                else:
                    print('Latest state loaded!')
            else:
                self.energy_data_dict = self.state.load_state(name)
            print('State loaded!')
    def store_state(self):
        name = self.state.store_state(self.energy_data_dict)
        print(f'State saved with name: {name} .')
        return name

    def save(self, key):
        if key != '__last_result__':
            return self.save_from_key(key)
        else:
            if self.buffer != None:
                self.saver.save_df(self.buffer[0], self.buffer[1])
                return self.buffer[1]
            else:
                return None

    @only_if_key_exists_decorator
    def save_from_key(self, key:dict.keys) -> str:
        d:energy_data = self.energy_data_dict.get(key)
        name = key + '_' + str(next(self.gen))
        self.saver.save_df(d.data, name)
        return name

    def return_data_keys(self, class_name:str=None):
        # Return list of keys (possibly, only the keys that correspond to a certain type of data)
        if class_name is None:
            return self.energy_data_dict.keys()
        else:
            key_list_to_loop_over = []
            for key in self.energy_data_dict.keys():
                if self.energy_data_dict[key].__class__.__name__ == class_name:
                    key_list_to_loop_over.append(key)
            return key_list_to_loop_over

    @only_if_key_exists_decorator
    def get_dataframe(self, key:dict.keys, all=False) -> None:
        d:energy_data = self.energy_data_dict.get(key)

        if all:
            # Return the whole dataframe.
            res = d.data
        else:
            # Return the first 5 rows of the data frame.
            res = d.data.head(PARAMS['number_of_rows_to_print_for_head'])

        return res

    @only_if_key_exists_decorator
    def get_min_max_day(self, key):
        d = self.energy_data_dict.get(key)
        return d.get_min_max()

    @only_if_multiple_keys_exist_decorator
    def get_min_max_day_from_keys(self, keys) -> None:

        # print("Time to print keys")
        min_day_all, max_day_all = dt.date(3100,10,1), dt.date(1900,1,1)

        for key in keys:
            # print(key)
            d = self.energy_data_dict.get(key)
            if min_day_all > d.min_day:
                min_day_all = d.min_day
            if max_day_all < d.max_day:
                max_day_all = d.max_day
        return min_day_all,max_day_all

    @only_if_multiple_keys_exist_decorator
    def energy_dist(self, keys, period, time_interval, b_d, b_h, is_total_provided, name):
        energy_data_list = []
        for _key in keys:
            d = self.energy_data_dict.get(_key)
            energy_data_list.append(d) # Add data to list
        res = energy_data.get_energy_distribution(energy_data_list, period= period, time_interval=time_interval, b_d=b_d, b_h=b_h, first_data_object_is_total_energy = is_total_provided)
        if res is None:
            return None
        if name is None or name == '':
            data_name = f"Energy_distribution_period_{get_daily_monthly_etc(period)}_start_date_{str(time_interval[0])}_end_date_{str(time_interval[1])}_{get_busines_day_yes_no_by_int(b_d)}_{get_busines_hours_yes_no_by_int(b_h)}"
        else:
            data_name = name

        if bool(PARAMS['always_keep']):
            self.keep_result(res, data_name, 'energy_distribution', period)

        self.buffer = (res, data_name, 'energy_distribution', period)

        if bool(PARAMS['always_save']):
            self.save_last_result()

        print(f'Distribution operation was made!')
        return data_name

    @only_if_one_key_exists_decorator  
    def get_indexes(self, key):
        d = self.energy_data_dict.get(key)
        tuple_of_lists, multiindex = d.get_keys()

        # If hourly period then agregate data by date.
        if d.period == 'H':
            if multiindex:
                tuple_of_lists = tuple_of_lists[0].normalize().unique(), tuple_of_lists[1].normalize().unique()
            else:
                tuple_of_lists = tuple_of_lists[0].normalize().unique(), []
        
        return tuple_of_lists, multiindex

    @only_if_one_key_exists_decorator
    def select_indexes(self,key,index_tuple_of_lists, name):

        if name is None or name == '':
            new_data_name = f"Selection_of_{key}_" + str(next(self.gen))
        else:
            new_data_name = name

        d = self.energy_data_dict.get(key)
        tuple_of_lists, multiindex = d.get_keys()

        if index_tuple_of_lists[0] is None:
            # User pressed x button.
            return

        if d.period == 'H':
            # function to expand a day into all the hours
            date_expander = lambda x: pd.date_range(x, x + datetime.timedelta(days=1), freq='H', inclusive='left')
            index_tuple_of_lists_all1 =pd.DatetimeIndex([]); index_tuple_of_lists_all2 = pd.DatetimeIndex([])
            if multiindex:
                index_tuple_of_lists_all1 = index_tuple_of_lists_all1.append([date_expander(x) for x in index_tuple_of_lists[0]])
                index_tuple_of_lists_all2 = index_tuple_of_lists_all2.append([date_expander(x) for x in index_tuple_of_lists[1]])

            else:
                index_tuple_of_lists_all1 = index_tuple_of_lists_all1.append([date_expander(x) for x in index_tuple_of_lists[0]])
            
            index_tuple_of_lists = (index_tuple_of_lists_all1, index_tuple_of_lists_all2)
        
        selection  = d.select(index_tuple_of_lists)

        if bool(PARAMS['always_keep']):
            self.keep_result(selection, new_data_name,  d.__class__.__name__, d.period)
        
        self.buffer = (selection, new_data_name,  d.__class__.__name__, d.period)

        if bool(PARAMS['always_save']):
            self.save_last_result()
        
        return new_data_name

    @only_if_one_key_exists_decorator
    def compare_typical_day(self, key:dict.keys, name):

        if name is None or name == '':
            new_data_name = f"Compare_typical_day_" + str(next(self.gen))
        else:
            new_data_name = name
        d = self.energy_data_dict.get(key)

        df_res = typical_day.compare(d)

        if df_res is None or df_res.empty:
            print("Nothing to show, operation returned empty data.")
            return
        print(df_res)

        if bool(PARAMS['always_keep']):
            self.keep_result(df_res, new_data_name, 'typical_day_comparison', d.period)
        
        self.buffer = (df_res, new_data_name, 'typical_day_comparison', d.period)

        if bool(PARAMS['always_save']):
            self.save_last_result()

        return new_data_name

    @only_if_one_key_exists_decorator
    def compare_distribution(self, key:dict.keys, name):

        if name is None or name == '':
            new_data_name = f"Compare_dists_" + str(next(self.gen))
        else:
            new_data_name = name
        d = self.energy_data_dict.get(key)

        df_res = energy_distribution.compare(d)

        if df_res is None or df_res.empty:
            print("Nothing to show, operation returned empty data.")
            return
        print(df_res)

        if bool(PARAMS['always_keep']):
            self.keep_result(df_res, new_data_name, 'energy_distribution_comparison', d.period)
        
        self.buffer = (df_res, new_data_name, 'energy_distribution_comparison', d.period)

        if bool(PARAMS['always_save']):
            self.save_last_result()

        return new_data_name

    @only_if_key_exists_decorator
    def compare_energy_stats(self, key:dict.keys, key2:dict.keys, outer_join, name, compare_months_aligned):
        
        d = self.energy_data_dict.get(key)
        d2 = self.energy_data_dict.get(key2)
        if name is None or name == '':
            data_name = f"Compare_stats_" + str(next(self.gen))
        else:
            data_name = name

        if d.period != d2.period:
            print("Chosen data must have the same period!")
            return None

        df_res = energy_stats_data.compare(d,d2, outer_join, compare_months_aligned)
        if df_res is None or df_res.empty:
            print("Nothing to show, operation returned empty data.")
            return 'empty data'
        # print(df_res)

        if bool(PARAMS['always_keep']):
            self.keep_result(df_res, data_name, 'energy_stats_comparison', d.period)
        
        self.buffer = (df_res, data_name, 'energy_stats_comparison', d.period)

        if bool(PARAMS['always_save']):
            self.save_last_result()
        
        return data_name

    @only_if_one_key_exists_decorator
    def typical_day(self, key:dict.keys, period, time_interval, b_d, b_h, name=None) -> None:
        # Typical day given a period.
        d:energy_data = self.energy_data_dict.get(key)
        
        res = d.get_typical_day(time_interval, b_d, b_h, period)
        if res is None:
            print("Operation failed, returning to main menu.")
            return
        if name is None or name == '':
            new_data_name = f"Typical_day_for_{key}_period_{get_daily_monthly_etc(period)}_start_date_{str(time_interval[0])}_end_date_{str(time_interval[1])}_{get_busines_day_yes_no_by_int(b_d)}_{get_busines_hours_yes_no_by_int(b_h)}"
        else:
            new_data_name = parse_name(name)

        if bool(PARAMS['always_keep']):
            self.keep_result(res, new_data_name, 'typical_day', period)

        self.buffer = (res, new_data_name, 'typical_day', period) # Contents in buffer are saved as tuple(dataframe, name, class_type, period)
        
        if bool(PARAMS['always_save']):
            self.save_last_result()

        return new_data_name


    @only_if_one_key_exists_decorator
    def energy_stats(self,key, period, time_interval, b_d, b_h, name=None):
        print(f"Energy Stats for {key}:")
        d:energy_data = self.energy_data_dict.get(key)
        res = d.get_energy_stats(period,time_interval, b_d, b_h) # Returns a dataframe.
        # print(res)
        if name is None or name == '':
            new_data_name = f"Energy_stats_for_{key}_period_{get_daily_monthly_etc(period)}_start_date_{str(time_interval[0])}_end_date_{str(time_interval[1])}_{get_busines_day_yes_no_by_int(b_d)}_{get_busines_hours_yes_no_by_int(b_h)}"
        else:
            new_data_name = parse_name(name)
        if bool(PARAMS['always_keep']):
            self.keep_result(res, new_data_name, 'energy_stats_data', period)

        self.buffer = (res, new_data_name, 'energy_stats_data', period) # Contents in buffer are saved as tuple(dataframe, name, class_type, period)
        
        if bool(PARAMS['always_save']):
            self.save_last_result()

        return new_data_name

    @only_if_multiple_keys_exist_decorator
    def resample(self, keys, period, name=None):

        for _key in keys:
            d = self.energy_data_dict.get(_key)
            res = d.resample(period= period)
            if name is None:
                data_name = d.name +'_resampled_period_' +  period
            else:
                data_name = name
            
            # if bool(PARAMS['always_keep']): Of course you want to keep those, otherwise, you lose them.
            self.keep_result(res, data_name, d.__class__.__name__, period)

            self.buffer = (res, data_name, d.__class__.__name__, period)

            if bool(PARAMS['always_save']):
                self.save_last_result()

        print(f'Resampling operation was made!')
        return keys

    def get_time_interval_dicts(self):
        return self.time_interval_dict_memory_start, self.time_interval_dict_memory_end

    def set_time_interval(self, start, stop):
        self.time_interval_dict_memory_start = {'year':start.year, 'month':start.month, 'day':start.day}
        self.time_interval_dict_memory_end = {'year':stop.year, 'month':stop.month, 'day':stop.day}
        print('Time interval was set successfully!')
        return 

    @only_if_key_exists_decorator
    def concatenate(self, key:dict.keys, key2:dict.keys, name=None) -> None:
        d = self.energy_data_dict.get(key)
        d2 = self.energy_data_dict.get(key2)
        # d, d2 should belong to same class in order to concatenate.
        try:
            assert d.__class__.__name__ == d2.__class__.__name__
        except:
            raise SameClassException

        df_res = Data.concatenate(d,d2)
        if name is None or name == '':
            new_data_name ='Concatenated_' + key + '_and_' + key2 # Create new key as the combination of the two keys.
        else:
            new_data_name = parse_name(name)
        # Add the newly created data to the dictionary.
        if bool(PARAMS['always_keep']):
            self.keep_result(df_res, new_data_name, d.__class__.__name__, d.period)
        # Add to buffer.
        self.buffer = (df_res, new_data_name, d.__class__.__name__, d.period)
        if bool(PARAMS['always_save']):
            self.save_last_result()
        return new_data_name

    @only_if_multiple_keys_exist_decorator
    def remove(self, keys) -> None:
        # Delete data tables with the specified keys.
        for _key in keys:
            _ = self.energy_data_dict.pop(_key)
            print(f'{_key} removed from list!')
        return

    @only_if_multiple_keys_exist_decorator
    def group(self, keys, name=None) -> None:
        if name is None or name == '':
            data_name = 'Grouped_' + str(next(self.gen))
        else:
            data_name = name
        energy_data_list = []

        for key in keys:
            d = self.energy_data_dict.get(key)
            energy_data_list.append(d) # Add data to list
        res = Data.group(energy_data_list)
        if res is None:
            print("Dataframe not saved because there was not a single shared index (timestamp).")
            raise InvalidSelectedDataException

        # Add the newly created data to the dictionary.
        if bool(PARAMS['always_keep']):
            self.keep_result(res, data_name, energy_data_list[0].__class__.__name__, energy_data_list[0].period)

        # Add to buffer.
        self.buffer = (res, data_name, energy_data_list[0].__class__.__name__, energy_data_list[0].period)
        print(f'Group operation was made!')

        if bool(PARAMS['always_save']):
            self.save_last_result()
        
        return data_name

    def save_last_result(self):
        if self.buffer != None:
            self.saver.save_df(self.buffer[0], self.buffer[1])
        else:
            print("Nothing to save so far!")

    def keep(self):
        if self.buffer is None:
                print('Nothing to keep yet!')
                return None
        self.keep_result(self.buffer[0], self.buffer[1], self.buffer[2], self.buffer[3])
        return self.buffer[1] # key

    def keep_result(self, data_energy:pd.DataFrame, name:str, class_type:str, period:str = None):
        if class_type == 'energy_data':
            data_d_type = energy_data(df = data_energy, name=name, period=period)
        elif class_type == 'energy_stats_data':
            data_d_type = energy_stats_data(period, df = data_energy, name=name)
        elif class_type == 'energy_distribution':
            data_d_type = energy_distribution(period, df = data_energy, name = name)
        elif class_type == 'energy_stats_comparison':
            data_d_type = energy_stats_comparison(period=period, df= data_energy, name = name)
        elif class_type == 'energy_distribution_comparison':
            data_d_type = energy_distribution_comparison(period=period, df= data_energy, name = name)
        elif class_type == 'typical_day':
            data_d_type = typical_day(period=period, df= data_energy, name = name)
        elif class_type == 'typical_day_comparison':
            data_d_type = typical_day_comparison(period=period, df= data_energy, name = name)
        else:
            # Other data type.
            data_d_type = Data(df = data_energy, name_of_data=name)

        self.energy_data_dict[name] = data_d_type
        print(f"Energy data kept in program memory. Refer to them with the name: '{name}'")


    def get_help_list_of_tuples(self):
        li = []
        li.append(("- help","-> Prints help message."))
        li.append(("- load data", "-> A popup file explorer opens for .xlsx or .csv file selection."))
        li.append(("- exit", "-> Exits this program."))
        li.append(("- show loaded data", "-> Prints the data loaded so far."))
        li.append(("- data head <name>", "-> Prints the first 5 rows of the data."))
        li.append(("- energy stats <name>", "-> Calculate sum, mean, min and max energy for a given time interval & frequency."))
        li.append(("- save result", "-> Save the last result in a file."))
        li.append(("- combine <name1> with <name2>", "-> Concatenate two dataframes."))
        li.append(("- compare energy stats <name1> [with <name2>]","-> Compare two stats data (axis aligned or outer join) or one stats data ."))# one stats data  with anti-merge join or axis aligned join on the period.)
        li.append(("- compare distribution <name1>","-> Compare distribution data (anti-merge join only)."))
        li.append(("- compare typical_day <name1>","-> Compare typical day data (anti-merge join only)."))
        li.append(("- save state","-> Save state so as to continue from where you left off."))
        li.append(("- load state <name>","-> Load specified state."))
        li.append(("- load latest state","-> Load previous state."))
        li.append(("- remove <name>","-> Removes the table with <name> from the list."))
        li.append(("- keep result in program","-> Keep the last result in program for future use."))
        li.append(("- group <name> <keys>","-> Group two or more loads into one (by addition)."))
        li.append(("- energy distribution <keys>","-> Get the distribution of energy across the loads."))
        li.append(("- select rows <name>","-> Select some rows from a given dataframe."))
        li.append(("- typical day <name>","-> Show the typical day for <name> data."))
        li.append(("- save <name>","-> Save selected data to the disk."))
        return li