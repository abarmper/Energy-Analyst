import sys, time, json, os, pickle, datetime, re
import pandas as pd

with open('params.json', 'r') as f_json:
    PARAMS = json.load(f_json)

def get_daily_monthly_etc(period:str):
    if period == 'M':
        return 'Monthly'
    elif period == 'D':
        return 'Daily'
    elif period == 'Y':
        return 'Yearly'
    elif period == 'W':
        return 'Weekly'
    elif period == 'Q':
        return 'Quarterly'
    elif period == 'H':
        return 'Hourly'
    else:
        raise ValueError(f'Input {period} is an invalid input!')

def get_busines_day_yes_no_by_int(bday:int):
    if bday == 0:
        return 'all_days'
    elif bday == 1:
        return 'business_days_only'
    elif bday == 2:
        return 'non_business_days_only'
    else:
        raise ValueError(f'Input {bday} is an invalid input!')

def get_busines_hours_yes_no_by_int(bhour:int):
    if bhour == 0:
        return 'all_hours'
    elif bhour == 1:
        return 'business_hours_only'
    elif bhour == 2:
        return 'non_business_hours_only'
    else:
        raise ValueError(f'Input {bhour} is an invalid input!')

def generaor_for_unamed_dataframes(max=996):
    for i in range(max):
        yield i

def print_slow(str, sleep_time=0.04):
    for letter in str:
        sys.stdout.write(letter)
        sys.stdout.flush()
        time.sleep(sleep_time)

def parse_name(name:str):
    name = name.strip() # Strip of any whitespace left or right.
    name = re.sub('\s+', '_', name) # Replace inner white spaces with _ .
    return name

def only_if_key_exists_decorator(fun):
    def wraper(self, key, key2=None, *arg, **kw):
        if key2 == None:
            # In this case, only one key is provided to the wrapped function.
            if key in self.energy_data_dict:
                return fun(self, key, *arg, **kw)
            else:
                # If key or key2 is not
                print("No loaded data with that name was found!")
                return None
        else:
            # The function requires two keys.
            key1_not_in_dict, key2_not_in_dict = (not key in self.energy_data_dict, not key2 in self.energy_data_dict)
            if (key1_not_in_dict) or (key2_not_in_dict):
                both_not_found = (key1_not_in_dict) and (key2_not_in_dict)
                print(f"Key(s) {key if key1_not_in_dict else ''}{' and ' if both_not_found else ''}{key2 if key2_not_in_dict else ''} were not found in the loaded data!")
                return None
            else:
                return fun(self, key, key2, *arg, **kw)
    return wraper

def only_if_one_key_exists_decorator(fun):
    def wraper(self, key, *arg, **kw):
        if key in self.energy_data_dict:
            return fun(self, key, *arg, **kw)
        else:
            print(f"No loaded data with that name was found! (key is {key})")
            return None
    return wraper

def only_if_multiple_keys_exist_decorator(fun):
    def wraper(self, keys,*arg, **kw): # removed name
        for key in keys:
            print("key:",key)
            if key in self.energy_data_dict:
                return fun(self, keys, *arg, **kw)# removed name
            else:
                # If key or key2 is not
                print(f"No loaded data with key: {key} was found!")
                return None
    return wraper

  
class results():
    def __init__(self):
            if bool(PARAMS['results_overwrite'] == 'True'):
                folder_name = 'Output'
            else:
                # Append time stamp so that each time we will have a new folder created.
                folder_name = 'Output_'+ datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            self.results_dir = os.path.join(os.getcwd(), folder_name)
            os.makedirs(self.results_dir, exist_ok=True)
            return

    def save_df(self, df:pd.DataFrame, name):
        # Change how floats are represented
        # df.wordnumber = df.wordnumber.astype(str)
        # df.wordnumber = df.wordnumber.apply(lambda x: x.replace('.',PARAMS['decimal_separator']))
        save_full_path_without_file_extention = os.path.join(self.results_dir,name)
        if 'excel' in PARAMS['type_of_tabular_output_file']:
            try:
                df.to_excel(save_full_path_without_file_extention + '.xlsx', index_label='DateTime')
            except PermissionError:
                print("No permission to write file! Maybe you have an opened file with the same name?")
                return
        if 'csv' in PARAMS['type_of_tabular_output_file']:
            try:
                df.to_csv(save_full_path_without_file_extention + '.csv', index_label='DateTime')
            except PermissionError:
                print("No permission to write file! Maybe you have an opened file with the same name?")
                return
        print(f'Result saved to file with name {name} under results sub-directory.')
        return

class state_saver():
    def __init__(self) -> None:
        folder_name = 'States'
        self.results_dir = os.path.join(os.getcwd(), folder_name)
        os.makedirs(self.results_dir, exist_ok=True)
        return

    def newest_path(self):
        files = os.listdir(self.results_dir)
        paths = [os.path.join(self.results_dir, basename) for basename in files]
        if paths == []:
            return None
        else:
            return max(paths, key=os.path.getctime)

    def if_file_exists_decorator(fun):
        def wraper(self, name, *arg, **kw):
            path = os.path.join(self.results_dir, name)
            if os.path.exists(path):
                return fun(self, path, *arg, **kw)
            else:
                print('File not found!')
        return wraper

    def store_state(self, diction):
        path = os.path.join(self.results_dir, 'state_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.pickle')
        with open(path, 'wb') as handle:
            pickle.dump(diction, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return 'state_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.pickle'

    def load_latest_state(self):
        path = self.newest_path()
        if path is None:
            print("No state available.")
            return dict()
        with open(path, 'rb') as handle:
            return pickle.load(handle)
    
    @if_file_exists_decorator
    def load_state(self, name):
        path = os.path.join(self.results_dir, name)
        with open(path, 'rb') as handle:
            return pickle.load(handle)

class InvalidSelectedDataException(Exception):
    "Dataframe not saved because there was not a single shared index (timestamp)."
    pass

class SameClassException(Exception):
    "Dataframes should belong to the same class."
    pass

class NoLastResultYetException(Exception):
    "The buffer is empty."
    pass

class NoPointInThisPeriod(ValueError):
    "Period should be chenged"
    pass
