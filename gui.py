import tkinter as tk
from tkinter import filedialog
import tkcalendar
from data_analysis import *
from functionality import *
from utils import *
import pandastable as pdt



class ScrollableFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        # create a canvas object and a vertical scrollbar for scrolling it
        self.vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.vscrollbar.pack(side='right', fill="y",  expand="false")
        self.canvas = tk.Canvas(self,
                                bg='#444444', bd=0,
                                height=350,
                                highlightthickness=0,
                                yscrollcommand=self.vscrollbar.set)
        self.canvas.pack(side="left", fill="both", expand="true")
        self.vscrollbar.config(command=self.canvas.yview)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = tk.Frame(self.canvas, **kwargs)
        self.canvas.create_window(0, 0, window=self.interior, anchor="nw")

        self.bind('<Configure>', self.set_scrollregion)


    def set_scrollregion(self, event=None):
        """ Set the scroll region on the canvas"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))


class SelectIndexes(ScrollableFrame):
    def __init__(self, parent, index_list, multiindex, name_field=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.name = ''
        self.name_box = name_field
        self.name_var = tk.StringVar(value='')

        self.key_list1 = []
        self.selections1 =[]
        self.key_list2 = []
        self.selections2 =[]
        self.keys1 = None
        self.keys2 = None

        self.interior.columnconfigure(0, weight=1)

        if multiindex:
            self.interior.columnconfigure(1, weight=1)

            # right_frame = ScrollableFrame(window)
            # right_frame.pack(side="right", fill="both", expand=True)

            for i, key in enumerate(index_list[0]):
                self.key_list1.append(key)
                var = tk.IntVar(value=0)
                self.selections1.append(var)
                c = tk.Checkbutton(self.interior, text=key, variable=var, onvalue=1, offvalue=0)
                c.grid(row=i,column=0, sticky='we')
                # text_left.window_create('end', window=c)
                # text_left.insert('end', '\n')

            for i, key in enumerate(index_list[1]):
                self.key_list2.append(key)
                var = tk.IntVar(value=0)
                self.selections2.append(var)
                c = tk.Checkbutton(self.interior, text=key, variable=var, onvalue=1, offvalue=0)
                c.grid(row=i,column=1, sticky='we')
                # text_right.window_create('end', window=c)
                # text_right.insert('end', '\n')

            # Btn = tk.Button(center_frame, height = 2, width = 4, text ="Apply", command = get_values_multi_index)
            # Btn.pack(anchor=tk.S, ipadx=20, ipady=20, fill=tk.X)
        else:
            # print(index_list[0])
            for i, key in enumerate(index_list[0]):
                self.key_list1.append(key)
                var = tk.IntVar(value=0)
                self.selections1.append(var)
                c = tk.Checkbutton(self.interior, text=key, variable=var, onvalue=1, offvalue=0)
                c.grid(row=i,column = 0, sticky='we')
        
    def _get_values_single_index(self):
        self.keys1=[]
        self.keys2=[]
        got_selections1 = list(map(lambda x: x.get(), self.selections1))
        self.keys1.extend([i for j,i in enumerate(self.key_list1) if got_selections1[j] == 1 ])

            # Btn = tk.Button(center_frame, height = 2, width = 4, text ="Apply", command = get_values_single_index)
            # Btn.pack(anchor=tk.S, ipadx=20, ipady=20, fill=tk.X)
        
            
    def _get_values_multi_index(self):
        self.keys1 = []
        self.keys2 = []
        got_selections1 = list(map(lambda x: x.get(), self.selections1))
        self.keys1.extend([i for j,i in enumerate(self.key_list1) if got_selections1[j] == 1 ])
        got_selections2 = list(map(lambda x: x.get(), self.selections2))
        self.keys2.extend([i for j,i in enumerate(self.key_list2) if got_selections2[j] == 1 ])


class SelectSamplePeriod(tk.LabelFrame):
    def __init__(self, parent, txt='', name_field=False, optional_period=True, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.name = ''
        self.name_box = name_field
        self.name_var = tk.StringVar(value='')
        self.p_var = tk.StringVar(value='default')
        self.period = None
        # Add label above radio button.
        self.config(text = txt)
        # Radio buttons for business days.
        R1 = tk.Radiobutton(self, text="Anualy.", variable=self.p_var, value='Y')
        R1.grid(sticky='ew')
        R2 = tk.Radiobutton(self, text="3 mont period (Quarter).", variable=self.p_var, value='Q')
        R2.grid(sticky='ew')
        R3 = tk.Radiobutton(self, text="Monthly", variable=self.p_var, value='M')
        R3.grid(sticky='ew')
        R3 = tk.Radiobutton(self, text="Weekly", variable=self.p_var, value='W')
        R3.grid(sticky='ew')
        R3 = tk.Radiobutton(self, text="Daily", variable=self.p_var, value='D')
        R3.grid(sticky='ew')
        R4 = tk.Radiobutton(self, text="Hourly", variable=self.p_var, value='H')
        R4.grid(sticky='ew')
        if optional_period:
            R5 = tk.Radiobutton(self, text="Default Period (.json)", variable=self.p_var, value='default')
            R5.grid(sticky='ew')

        if self.name_box:
            tk.Label(self, text='Name for the new data (optional):', justify='center').grid(sticky='sew')
            inputtxt = tk.Entry(self, width = 30, textvariable=self.name_var, justify='center')
            inputtxt.grid(sticky='sew')

    def _get_values(self):
        self.period = self.p_var.get() if self.p_var.get() != 'default' else None
        if self.name_box:
            self.name = self.name_var



class DistributionSelect(tk.LabelFrame):
    def __init__(self, parent,  key_list_to_loop_over, txt='', name_field=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.start = None
        self.stop = None
        self.config(text=txt)
        self.parent = parent
        self.selections =[]
        self.got_selections = None
        self.key_list = []
        self.keys_result = None
        self.var_radio = tk.IntVar(value=-1)
        self.radio = None
        self.is_total_provided = None
        self.name = ''
        self.name_var = tk.StringVar()
        self.name_box = name_field
 
        # window.geometry('100x500')
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        left_frame = tk.LabelFrame(self, text='Datasets In Distribution:')
        left_frame.grid(column=0, row=0, sticky='w')
        right_frame = tk.LabelFrame(self, text='Which one is the Total?')
        right_frame.grid(column=1, row=0, sticky='w')

        for i, key in enumerate(key_list_to_loop_over):
            self.key_list.append(key)
            var = tk.IntVar()
            self.selections.append(var)
            c = tk.Checkbutton(left_frame, text=key, variable=var, onvalue=1, offvalue=0)
            c.grid(column=0, sticky='w')
            r = tk.Radiobutton(right_frame, text=key, variable=self.var_radio, value=i)
            r.grid(column=1, sticky="w")
        # No Total Provided radio button.
        r = tk.Radiobutton(self, text="No Total Energy Provided", variable=self.var_radio, value=-1) # If no total energy is provided
        r.grid(column = 1, row=97, sticky=tk.NE)

        if name_field:
            tk.Label(self, text='Name for the new data (optional):', justify='center').grid(columnspan=2, column=0, row = 98,sticky='s')
            inputtxt = tk.Entry(self, width = 30, textvariable=self.name_var, justify='center')
            inputtxt.grid(columnspan=2, column=0)

    def _get_values(self):
        self.keys_result=[]
        if self.var_radio.get() != -1:
            self.is_total_provided = True
            self.keys_result.append(self.key_list[self.var_radio.get()]) # Total key is first
            # If someone presses the radio button without the checkbox, it's ok. The radio button adds it to the list (no need to press both).
        else:
            self.is_total_provided = False
        self.got_selections = list(map(lambda x: x.get(), self.selections))
        self.keys_result.extend([i for j,i in enumerate(self.key_list) if (self.got_selections[j] == 1 and j != self.var_radio.get()) ])
        
        if self.name_box:
            self.name = parse_name(self.name_var.get())
        

        
        
        # Btn = tk.Button(center_frame, height = 2, width = 4, text ="Apply", command = self._get_values)
        # Btn.pack(anchor=tk.S, ipadx=20, ipady=20, fill=tk.X)
        
        return

class DateSelect(tk.LabelFrame):
    def __init__(self, parent, min_d, max_d, time_interval_start, time_interval_stop, optional_period=False, txt='', *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.start = None
        self.stop = None
        self.config(text=txt)
        self.parent = parent
        self.var_bd = tk.IntVar() # For business days (used in radio buttons)
        self.var_bh = tk.IntVar() # For Business hours
        self.bd = None
        self.bh = None
        self.period = None
        self.p_var = tk.StringVar(value='M')
        date_frame = tk.LabelFrame(self, text='Date Selection')
        date_frame.pack()
        tk.Label(date_frame, text='From:').pack()
        self.date1 = tkcalendar.DateEntry(date_frame, select_mode='date', mindate = min_d, maxdate=max_d,  **time_interval_start, showothermonthdays =False, date_pattern='y-mm-dd')
        self.date1.pack(padx=10,pady=10)

        tk.Label(date_frame, text='To:').pack()
        self.date2 = tkcalendar.DateEntry(date_frame, select_mode='date', mindate = min_d, maxdate=max_d, **time_interval_stop, showothermonthdays =False, date_pattern='y-mm-dd')
        self.date2.pack(padx=10,pady=10)

        # Add label above radio button.
        l2 = tk.LabelFrame(self, text = "Choose time period.")
        l2.pack(anchor = tk.W)
        # Radio buttons for business days.
        R1 = tk.Radiobutton(l2, text="Anualy.", variable=self.p_var, value='Y')
        R1.pack( anchor = tk.W )
        R2 = tk.Radiobutton(l2, text="3 mont period (Quarter).", variable=self.p_var, value='Q')
        R2.pack( anchor = tk.W )
        R3 = tk.Radiobutton(l2, text="Monthly", variable=self.p_var, value='M')
        R3.pack( anchor = tk.W)
        R3 = tk.Radiobutton(l2, text="Weekly", variable=self.p_var, value='W')
        R3.pack( anchor = tk.W)
        R3 = tk.Radiobutton(l2, text="Daily", variable=self.p_var, value='D')
        R3.pack( anchor = tk.W)
        R4 = tk.Radiobutton(l2, text="Hourly", variable=self.p_var, value='H')
        R4.pack( anchor = tk.W)
        if optional_period:
            R5 = tk.Radiobutton(l2, text="No Period", variable=self.p_var, value='no_period')
            R5.pack( anchor = tk.W)

        # Add label above radio button.
        l3 = tk.LabelFrame(self, text = "Business day filter?")
        l3.pack(anchor = tk.W)
        # Radio buttons for business days.
        R1_bd = tk.Radiobutton(l3, text="Business and non business days.", variable=self.var_bd, value=0)
        R1_bd.pack( anchor = tk.W )
        R2_bd = tk.Radiobutton(l3, text="Only Business days.", variable=self.var_bd, value=1)
        R2_bd.pack( anchor = tk.W )
        R3_bd = tk.Radiobutton(l3, text="Only non business days", variable=self.var_bd, value=2)
        R3_bd.pack( anchor = tk.W)

        # Add label above radio button.
        l4 = tk.LabelFrame(self, text = "Business hour filter?")
        l4.pack(anchor = tk.W)
        # Radio buttons for business days.
        R1_bh = tk.Radiobutton(l4, text="Business and non business hours.", variable=self.var_bh, value=0)
        R1_bh.pack( anchor = tk.W )
        R2_bh = tk.Radiobutton(l4, text="Only Business hours.", variable=self.var_bh, value=1)
        R2_bh.pack( anchor = tk.W )
        R3_bh = tk.Radiobutton(l4, text="Only non business hours", variable=self.var_bh, value=2)
        R3_bh.pack( anchor = tk.W)


        # tk.Button(self,text='Apply',command=lambda: self.loop_if_invalid_dates(date1.get_date(), date2.get_date())).pack() 


        # return dates, var_bd.get(), var_bh.get(), var.get()


    def _get_dates(self):
        self.period = self.p_var.get()
        self.start = self.date1.get_date()
        self.stop = self.date2.get_date()
        self.bd = self.var_bd.get()
        self.bh = self.var_bh.get()
        
        # if self.start <= self.stop:
        #     root.destroy() # Ok, destroy window.
        # else:
        #     # Not ok yet. Loop again.
        #     tk.messagebox.showwarning("Warning", "Invalid Dates!\nEnd date should follow start date.")
    



class RadioDataset(tk.LabelFrame):
    def __init__(self, parent, key_list_to_loop_over, name_field=False, outer=False, aligne_months=False, text='', only_head=False, last_result=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Set the label of the Frame.
        self.name_field = name_field
        self.config(text=text)
        self.parent = parent
        self.key_list = []
        self.key_var = tk.IntVar()
        self.key = None
        self.outer = None
        self.aligne = None
        self.only_head_box = only_head
        self.yes_to_head = None
        if only_head:
            self.yes_to_head_var = tk.BooleanVar()
        if name_field:
            self.name_var = tk.StringVar()
        self.last_result_radio = last_result
        self.name = ''
        self.outer_join_box = outer
        self.outer_var = tk.BooleanVar(value=False)
        self.aligne_months_box = aligne_months
        self.aligne_var = tk.BooleanVar(value=False)



        for i, _key in enumerate(key_list_to_loop_over):
            self.key_list.append(_key)
            r = tk.Radiobutton(self, text=_key, variable=self.key_var, value=i)
            r.grid(sticky='w')

        if self.last_result_radio:
            r = tk.Radiobutton(self, text='save latest result', variable=self.key_var, value=-1)
            r.grid(sticky='w')

        if name_field:
            tk.Label(self, text='Name for the new data (optional):', justify='center').grid(row = 98,sticky='s')
            inputtxt = tk.Entry(self, width = 30, textvariable=self.name_var, justify='center')
            inputtxt.grid(row = 99, sticky='s')
        
        if self.outer_join_box:
            c = tk.Checkbutton(self, text="Outer Join", variable=self.outer_var, onvalue=1, offvalue=0, justify='right')
            c.grid(sticky=tk.E)

        if self.only_head_box:
            c_all = tk.Checkbutton(self, text="Just The Top Rows", variable=self.yes_to_head_var, onvalue=1, offvalue=0, justify='right')
            c_all.grid(sticky=tk.E)

        if self.aligne_months_box:
            cm = tk.Checkbutton(self, text="Align Period", variable=self.aligne_var, onvalue=1, offvalue=0, justify='right')
            cm.grid(sticky=tk.E)

        # Btn = tk.Button(self, height = 2, width = 4, text ="Apply", command = self._get_values)
        # Btn.pack()

    def _get_values(self):
        if self.last_result_radio and self.key_var.get() == -1:
            self.key = '__last_result__'
        else:
            if self.key_list != []:
                self.key = self.key_list[self.key_var.get()]
            else:
                self.key = None
        if self.aligne_months_box:
            self.aligne = self.aligne_var.get()

        if self.outer_join_box:
            self.outer = self.outer_var.get()

        if self.name_field:
            self.name = parse_name(self.name_var.get())

        if self.only_head_box:
            self.yes_to_head = self.yes_to_head_var.get()

class CheckBoxDataset(tk.LabelFrame):
    def __init__(self, parent, key_list_to_loop_over, name_field=False, text='', *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Set the label of the Frame.
        self.name_field = name_field
        self.config(text=text)
        self.parent = parent
        self.key_list = []
        self.key_vars = []
        self.selected_keys = None
        if name_field:
            self.name_var = tk.StringVar()
        self.name = ''

        for i, _key in enumerate(key_list_to_loop_over):
            self.key_list.append(_key)
            var = tk.IntVar()
            self.key_vars.append(var)
            c = tk.Checkbutton(self, text=_key, variable=var, onvalue=1, offvalue=0)
            c.grid(sticky='we')

        if name_field:
            tk.Label(self, text='Name for the new data (optional):', justify='center').grid(row=98, sticky='s')
            inputtxt = tk.Entry(self, width = 30, textvariable=self.name_var, justify='center')
            inputtxt.grid(row = 99, sticky='s')
        

        # Btn = tk.Button(self, height = 2, width = 4, text ="Apply", command = self._get_values)
        # Btn.pack()

    def _get_values(self):
        got_selections = list(map(lambda x: x.get(), self.key_vars))

        self.selected_keys =  [i for j,i in enumerate(self.key_list) if got_selections[j] == 1]

        if self.name_field:
            self.name = parse_name(self.name_var.get())


class MainFrame(tk.Frame):
    def __init__(self, parent, functions_class, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.backbone = functions_class
        self.parent = parent
        self.parent.protocol('WM_DELETE_WINDOW',self._on_close)
        self.key = None
        

        tk.Label(self, text="Energy Analyst", font=('Times 20'), width=18, height=3, bg='yellow').grid(column=0, row=0,sticky='new', pady=(0,5))
        
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=1)
        self.rowconfigure(2,weight=1)
        self.rowconfigure(3,weight=1)
        self.rowconfigure(4,weight=1)
        # side-by-side layout
        # tk.Button(text='help', command=self._help_message).grid(column=1, row=1)
        
        r_info = tk.LabelFrame(self, text='Data Load and Data Management')
        r_info.grid(sticky=(tk.W + tk.E))
        for i in range(3):
            r_info.columnconfigure(i, weight=1)
        tk.Button(r_info, text='Load Data', height=2, command= self._load_data).grid(column=0, columnspan=1, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(r_info, text='Show Data', height=2, command = self._show_loaded_data).grid(column=1, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(r_info, text='Resample', height=2, command = self._resample).grid(column=2, row=0, sticky='ew', padx=10, pady=5)

        tk.Button(r_info, text='Concatenate', height=2, command=self._concat).grid(column=0, row=1, sticky='ew', padx=10, pady=5)
        tk.Button(r_info, text='Group', height=2, command= self._group).grid(column=1, row=1, sticky='ew', padx=10, pady=5)
        tk.Button(r_info, text='Show', height=2, command= self._show_table).grid(column=2, row=1, sticky='ew', padx=10, pady=5)

        tk.Button(r_info, text='Save', height=2, command=self._save).grid(column=0, row=2, sticky='ew', padx=10, pady=5)
        tk.Button(r_info, text='Keep', height=2, command=self._keep).grid(column=1, row=2, sticky='ew', padx=10, pady=5)
        tk.Button(r_info, text='Remove', height=2, command=self._remove).grid(column=2, row=2, sticky='ew', padx=10, pady=5)

        en_stats = tk.LabelFrame(self, text='Energy Statistics')
        en_stats.grid(sticky=(tk.W + tk.E), pady=5)
        for i in range(3):
            en_stats.columnconfigure(i, weight=1)
        tk.Button(en_stats, text='Stats', height=2, width=8, command=self._show_stats).grid(column=0, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(en_stats, text='Distribution', height=2, width=8, command=self._get_distribution).grid(column=1, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(en_stats, text='Typical Day', height=2, width=8, command=self._typical_day).grid(column=2, row=0, sticky='ew', padx=10, pady=5)

        comparisons = tk.LabelFrame(self, text='Comparisons')
        comparisons.grid(sticky=(tk.W + tk.E), pady=5)
        for i in range(3):
            comparisons.columnconfigure(i, weight=1)
        tk.Button(comparisons, text='Energy Stats', height=2, command=self._compare_stats).grid(column=0, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(comparisons, text='Distributions', height=2, command=self._compare_dists).grid(column=1, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(comparisons, text='Typical Days', height=2, command=self._compare_typical_day).grid(column=2, row=0, sticky='ew', padx=10, pady=5)

        state = tk.LabelFrame(self, text='Program\'s state')
        state.grid(sticky=(tk.W + tk.E), pady=5)
        for i in range(3):
            state.columnconfigure(i, weight=1)
        
        tk.Button(state, text='Save State', height=2, command= self._save_state).grid(column=0,  row=0, sticky='ew', padx=10, pady=5)
        tk.Button(state, text='Load State', height=2, command= self._load_latest_state).grid(column=1, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(state, text='Load <name>', height=2, command=self._load_state).grid(column=2, row=0, sticky='ew', padx=10, pady=5)

        other = tk.LabelFrame(self, text='Other Commands')
        other.grid(sticky=(tk.W + tk.E), pady=5)
        for i in range(3):
            other.columnconfigure(i, weight=1)
        tk.Button(other, text='Select', height=2, command=self._select).grid(column=0, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(other, text='Help', height=2, command=self._help_message).grid(column=1, row=0, sticky='ew', padx=10, pady=5)
        tk.Button(other, text='Exit', height=2, command = self._on_close).grid(column=2, row=0, sticky='ew', padx=10, pady=5)


        # Status Bar
        self.status_variable = tk.StringVar()
        self.status_variable_color = tk.StringVar()
        # self.status_variable_color.set('blue')
        self.status = tk.Label(self, textvariable=self.status_variable, width=60, height=3)
        self.status.grid(sticky=tk.W + tk.E, row=99, padx=10)
        # Resate state in every click.
        self.parent.bind('<Button>',self._reset_status)

    def _load_state(self):
        def _get_name(window, name):
            window.destroy()
            if name == '':
                self._status_set(f'Name was not set!', 'red')
                return
            try:
                self.backbone.load_latest_state(name)
            except:
                self._status_set(f'State was not loaded!', 'red')
            else:
                self._status_set(f'State was loaded!', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Type State's Name.")
        new_window.columnconfigure(0, weight=1)
        
        name_var = tk.StringVar(value='')
        tk.Label(new_window, text='Name for the new data (optional):').grid(columnspan=2, sticky='we')
        tk.Entry(new_window, textvariable=name_var, justify='center').grid(columnspan=2, sticky='we')
        
        tk.Button(new_window, text='Load', command=lambda: _get_name(new_window, name_var.get())).grid(sticky='sew')
        
        self.backbone.load_latest_state()

    def _load_latest_state(self):
        try:
            self.backbone.load_latest_state()
        except:
            self._status_set(f'Latest state was not loaded!', 'red')
        else:
            self._status_set(f'Latest state was loaded!', 'green')

    def _save_state(self):
        try:
            name =  self.backbone.store_state()
            if name is not None:
                self._status_set(f'State saved!\nName: {name}', 'green')
            else:
                self._status_set(f'State was not saved!', 'red')
        except:
            self._status_set(f'State was not saved!', 'red')
        else:
            self._status_set(f'State saved!\nName: {name}', 'green')

    def _on_close(self):
        response=tk.messagebox.askyesno('Exit','Are you sure you want to exit?')
        if response:
            self.parent.destroy()

    def _select(self):
        def _get_1_key_and_select_dates(self, frame, window):

            def _get_indexes(self,frame_last, window_last, key, multiindex,  nm):
                if multiindex:
                    frame_last._get_values_multi_index()
                    index_tuple_of_lists = (frame_last.keys1, frame_last.keys2)
                else:
                    frame_last._get_values_single_index()
                    index_tuple_of_lists = (frame_last.keys1, None)

                if frame_last.keys1 == []:
                    print("No keys selected!")
                    self._status_set(f'No keys selected!', 'red')
                    return
                
                window_last.destroy()


                try:
                    name = self.backbone.select_indexes(key, index_tuple_of_lists, parse_name(nm))
                    if name is None:
                        self._status_set(f'Selection was unsuccessfull!', 'red')
                        return
                except:
                    self._status_set(f'Selection was unsuccessfull!', 'red')
                    return
                else:
                    self._status_set(f'Selection was successfull!\nName: {name}', 'green')

                
            frame._get_values()
            key1= frame.key
            nm = frame.name
            window.destroy()

            # Check if key is not none
            if key1 is None:
                self._status_set(f'Dataset selection was unsuccessfull.', 'red')
                return
            
            # Get min max day. It is also a way to check that key exists in dictionary.
            res = self.backbone.get_indexes(key1)
            if res is None: return # It means that key was not found.
            tuple_of_lists, multi_index = res

            # Use the entered key to make another window.
            new_window = tk.Toplevel(self)
            new_window.title("Select Indexes.")
            new_window.columnconfigure(0, weight=1)
            
            frame2 = SelectIndexes(new_window,tuple_of_lists, multi_index)
            frame2.grid(column=0, row=0, sticky='ew')

            tk.Button(new_window, text='Select Idx', command=lambda: _get_indexes(self,frame2, new_window, key1,multi_index,nm)).grid(sticky='sew')
            return

        new_window = tk.Toplevel(self)
        new_window.title("Select Data For Filter.")
        new_window.columnconfigure(0, weight=1)
        frame = RadioDataset(new_window, self.backbone.return_data_keys(), name_field=True)
        frame.grid(column=0, row=0, sticky='ew')
        
        tk.Button(new_window, text='Select Dataset', command=lambda: _get_1_key_and_select_dates(self, frame, new_window)).grid(sticky='sew')
        # Block until button is pressed.
        # new_window.mainloop()
        

    def _compare_typical_day(self):
        def _get_1_key_and_show(frame, window, nm):
            frame._get_values()
            window.destroy()
            # Now get the key (not from the variable attached to radio widgets).
            key1= frame.key
            
            if key1 is None:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            try:
                name = self.backbone.compare_typical_day(key1, parse_name(nm))
                if name is None:
                    self._status_set(f'Comparison of typical day failed!\nCheck the input data.', 'red')
                    return
            except:
                self._status_set(f'Comparison of typical day failed!', 'red')
                return
            else:
                self._status_set(f'Comparison of typical day was successfull!\nName: {name}.', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Select Typical Day For Comparison.")
        new_window.columnconfigure(0, weight=1)
        frame = RadioDataset(new_window, self.backbone.return_data_keys('typical_day'), last_result=False)
        frame.grid(column=0, row=0, sticky='ew')
        name_var = tk.StringVar(value='')
        tk.Label(new_window, text='Name for the new data (optional):').grid(columnspan=2, sticky='we')
        tk.Entry(new_window, textvariable=name_var, justify='center').grid(columnspan=2, sticky='we')
        
        tk.Button(new_window, text='Save', command=lambda: _get_1_key_and_show(frame, new_window, name_var.get())).grid(sticky='sew')
        

    def _compare_dists(self):
        def _get_1_key_and_show(frame, window, nm):
            frame._get_values()
            window.destroy()
            # Now get the key (not from the variable attached to radio widgets).
            key1= frame.key
            
            if key1 is None:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            try:
                name = self.backbone.compare_distribution(key1, parse_name(nm))
                if name is None:
                    self._status_set(f'Comparison of distributions failed!\nCheck the input data.', 'red')
                    return
            except:
                self._status_set(f'Comparison of distributions failed!', 'red')
                return
            else:
                self._status_set(f'Comparison of distributions was successfull!\nName: {name}.', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Select Distributions For Comparison.")
        new_window.columnconfigure(0, weight=1)
        frame = RadioDataset(new_window, self.backbone.return_data_keys('energy_distribution'), last_result=False)
        frame.grid(column=0, row=0, sticky='ew')
        name_var = tk.StringVar(value='')
        tk.Label(new_window, text='Name for the new data (optional):').grid(columnspan=2, sticky='we')
        tk.Entry(new_window, textvariable=name_var, justify='center').grid(columnspan=2, sticky='we')
        
        tk.Button(new_window, text='Save', command=lambda: _get_1_key_and_show(frame, new_window, name_var.get())).grid(sticky='sew')
        


    def _get_distribution(self):
        def _get_1_key_and_get_date(self, frame, window):

            def _get_dates_for_dist(self,frame_last, window_last, keys_all, is_total_prov, nm):
                frame_last._get_dates()
                start = frame_last.start
                stop = frame_last.stop
                per = frame_last.period
                bd = frame_last.bd
                bh = frame_last.bh
                
                if per is None:
                    tk.messagebox.showwarning("Warning", "Invalid Period!")
                    return # Meaning that you have to re-enter dates.
                if start > stop:
                    tk.messagebox.showwarning("Warning", "Invalid Dates!\nEnd date should follow start date.")
                    return # Meaning that you have to re-enter dates.
                window_last.destroy()
                # Svae the dates for easy loading the next time (no need to type them again).
                self.backbone.set_time_interval(start, stop)

                try:
                    name = self.backbone.energy_dist(keys_all, per, (start,stop), bd, bh, is_total_prov, nm)
                    if name is None:
                        self._status_set(f'Generation of distribution was unsuccessfull!', 'red')
                        return
                except Exception as e:
                    print(e)
                    self._status_set(f'Generation of distribution was unsuccessfull!', 'red')
                    return
                else:
                    self._status_set(f'Generation of distribution was successfull!\nName: {name}', 'green')
                return


            frame._get_values()
            window.destroy()
            key1_all = frame.keys_result
            # Check if key is not none
            if key1_all is None or key1_all == []:
                self._status_set(f'Dataset selection was unsuccessfull.', 'red')
                return
            is_total_first = frame.is_total_provided
            nm = frame.name

            # Get min max day from all of the keys.
            dates = self.backbone.get_min_max_day_from_keys(key1_all)
            if dates is None: return # It means that key was not found.
            min_d, max_d = dates

            # Use the entered keys to make another window.
            new_window = tk.Toplevel(self)
            new_window.title("Select Date Range.")
            new_window.columnconfigure(0, weight=1)
            
            # Remember the previously selected dates.
            previous_start_date, previous_stop_date = self.backbone.get_time_interval_dicts()
            frame2 = DateSelect(new_window,min_d, max_d, previous_start_date, previous_stop_date)
            frame2.grid(column=0, row=0, sticky='ew')
            tk.Button(new_window, text='Select Dates', command=lambda: _get_dates_for_dist(self,frame2, new_window, key1_all, is_total_first, nm)).grid(sticky='sew')


        new_window = tk.Toplevel(self)
        new_window.title("Select Data For Distribution.")
        new_window.columnconfigure(0, weight=1)
        frame = DistributionSelect(new_window, self.backbone.return_data_keys('energy_data'), name_field=True)
        frame.grid(column=0, row=0, sticky='ew')

        tk.Button(new_window, text='Show Distribution', command=lambda: _get_1_key_and_get_date(self, frame, new_window)).grid(sticky='sew')
    
    def _compare_stats(self):
        def _get_2_keys_and_close(frame1, frame2, window, nm=None, outer=False, axis_aligned=False):
            frame1._get_values()
            frame2._get_values()
            window.destroy()
            # Now get the keys (not from the variables attached to widgets).
            key1, key2 = frame1.key, frame2.key
            if key1 is None or key2 is None:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            if axis_aligned == True and outer == False:
                self._status_set(f'You can not have period axis aligned checked and outer join not checked!', 'red')
                return
            try:
                name = self.backbone.compare_energy_stats(key1, key2, outer, parse_name(nm), axis_aligned)
                if name is None:
                    self._status_set(f'Comparison was unsuccessfull!\nMaybe different periods?', 'red')
                if name == 'empty data':
                    self._status_set(f'Comparison was unsuccessfull!\nTry axis not aligned and outer join.', 'red')
            except Exception as e:
                print(e)
                self._status_set(f'Comparison was unsuccessfull!', 'red')
            else:
                self._status_set(f'Comparison was successfull!\nCombined {key1} with {key2}\nName: {name}.', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Select Energy Data To Compare With.")
        new_window.columnconfigure(0, weight=1)
        new_window.columnconfigure(1, weight=1)
        frame1 = RadioDataset(new_window, self.backbone.return_data_keys('energy_stats_data'))
        frame1.grid(column=0, row=0, sticky='ew')
        frame2 = RadioDataset(new_window, self.backbone.return_data_keys('energy_stats_data'))
        frame2.grid(column=1, row=0, sticky='ew')
        name_var = tk.StringVar(value='')
        tk.Label(new_window, text='Name for the new data (optional):').grid(columnspan=2, sticky='we')
        tk.Entry(new_window,textvariable=name_var, justify='center').grid(columnspan=2, sticky='we')
        outer = tk.BooleanVar(value=False)
        tk.Checkbutton(new_window, text='outer join', variable=outer).grid(columnspan=2, sticky='we')
        axis_aligned = tk.BooleanVar(value=False)
        tk.Checkbutton(new_window, text='period axis aligned', variable=axis_aligned).grid(columnspan=2, sticky='we')
        tk.Button(new_window, text='Apply', command=lambda: _get_2_keys_and_close(frame1, frame2, new_window, name_var.get(), outer.get(), axis_aligned.get())).grid(columnspan=2, sticky='sew')
        

    def _show_stats(self):
        def _get_1_key_and_select_dates(self, frame, window):
            def _get_dates(self,frame_last, window_last, key, nm):
                frame_last._get_dates()
                start = frame_last.start 
                stop = frame_last.stop 
                per = frame_last.period
                bd = frame_last.bd 
                bh = frame_last.bh 
                # print('keyyy', key)
                if per is None:
                    tk.messagebox.showwarning("Warning", "Invalid Period!")
                    return # Meaning that you have to re-enter dates.
                if start > stop:
                    tk.messagebox.showwarning("Warning", "Invalid Dates!\nEnd date should follow start date.")
                    return # Meaning that you have to re-enter dates.
                window_last.destroy()
                # Svae the dates for easy loading the next time (no need to type them again).
                self.backbone.set_time_interval(start, stop)

                try:
                    name = self.backbone.energy_stats(key, per, (start, stop), bd, bh, nm)
                    if name is None:
                        self._status_set(f'Generation of statistics was unsuccessfull!', 'red')
                        return
                except:
                    self._status_set(f'Generation of statistics was unsuccessfull!', 'red')
                    return
                else:
                    self._status_set(f'Generation of statistics was successfull!\nName: {name}', 'green')
                    

                
            frame._get_values()
            key1= frame.key
            nm = frame.name
            window.destroy()

            # Check if key is not none
            if key1 is None:
                self._status_set(f'Dataset selection was unsuccessfull.', 'red')
                return
            
            # Get min max day. It is also a way to check that key exists in dictionary.
            dates = self.backbone.get_min_max_day(key1)
            if dates is None: return # It means that key was not found.
            min_d, max_d = dates

            # Use the entered key to make another window.
            new_window = tk.Toplevel(self)
            new_window.title("Select Date Range.")
            new_window.columnconfigure(0, weight=1)
            
            # Remember the previously selected dates.
            previous_start_date, previous_stop_date = self.backbone.get_time_interval_dicts()
            frame2 = DateSelect(new_window,min_d, max_d, previous_start_date, previous_stop_date)
            frame2.grid(column=0, row=0, sticky='ew')
            tk.Button(new_window, text='Select Dates', command=lambda: _get_dates(self,frame2, new_window, key1, nm)).grid(sticky='sew')
            return

        new_window = tk.Toplevel(self)
        new_window.title("Select Energy Data.")
        new_window.columnconfigure(0, weight=1)
        frame = RadioDataset(new_window, self.backbone.return_data_keys('energy_data'), name_field=True)
        frame.grid(column=0, row=0, sticky='ew')
        
        tk.Button(new_window, text='Select Dataset', command=lambda: _get_1_key_and_select_dates(self, frame, new_window)).grid(sticky='sew')
        # Block until button is pressed.
        # new_window.mainloop()


    def _typical_day(self):
        def _get_1_key_and_select_dates(self, frame, window):
            def _get_typical_day(self,frame_last, window_last, key, nm):
                frame_last._get_dates()
                start = frame_last.start 
                stop = frame_last.stop 
                per = frame_last.period
                bd = frame_last.bd 
                bh = frame_last.bh 
                # print('keyyy', key)
                if per is None:
                    tk.messagebox.showwarning("Warning", "Invalid Period!")
                    return # Meaning that you have to re-enter dates.
                if start > stop:
                    tk.messagebox.showwarning("Warning", "Invalid Dates!\nEnd date should follow start date.")
                    return # Meaning that you have to re-enter dates.
                window_last.destroy()
                # Svae the dates for easy loading the next time (no need to type them again).
                self.backbone.set_time_interval(start, stop)

                try:
                    name = self.backbone.typical_day(key, per, (start, stop), bd, bh, nm)
                    if name is None:
                        self._status_set(f'Generation of typical day was unsuccessfull!\nCheck the time period.', 'red')
                        return
                except:
                    self._status_set(f'Generation of typical day was unsuccessfull!', 'red')
                    return
                else:
                    self._status_set(f'Generation of typical day was successfull!\nName: {name}', 'green')
                    

            frame._get_values()
            key1= frame.key
            nm = frame.name
            window.destroy()

            # Check if key is not none
            if key1 is None:
                self._status_set(f'Dataset selection was unsuccessfull.', 'red')
                return
            
            # Get min max day. It is also a way to check that key exists in dictionary.
            dates = self.backbone.get_min_max_day(key1)
            if dates is None: return # It means that key was not found.
            min_d, max_d = dates

            # Use the entered key to make another window.
            new_window = tk.Toplevel(self)
            new_window.title("Select Date Range.")
            new_window.columnconfigure(0, weight=1)
            
            # Remember the previously selected dates.
            previous_start_date, previous_stop_date = self.backbone.get_time_interval_dicts()
            frame2 = DateSelect(new_window,min_d, max_d, previous_start_date, previous_stop_date)
            frame2.grid(column=0, row=0, sticky='ew')
            tk.Button(new_window, text='Select Dates', command=lambda: _get_typical_day(self,frame2, new_window, key1, nm)).grid(sticky='sew')
            return

        new_window = tk.Toplevel(self)
        new_window.title("Select Energy Data.")
        new_window.columnconfigure(0, weight=1)
        frame = RadioDataset(new_window, self.backbone.return_data_keys('energy_data'), name_field=True)
        frame.grid(column=0, row=0, sticky='ew')
        
        tk.Button(new_window, text='Select Dataset', command=lambda: _get_1_key_and_select_dates(self, frame, new_window)).grid(sticky='sew')
        # Block until button is pressed.
        # new_window.mainloop()


    def _keep(self):
        rs = self.backbone.keep()
        if rs is None:
            self._status_set(f'Nothing to keep yet!', 'red')
        else:
            self._status_set(f'Kept {rs} in program memory!', 'green')

    def _save(self):
        def _get_1_key_and_show(frame, window):
            frame._get_values()
            window.destroy()
            # Now get the key (not from the variable attached to radio widgets).
            key1= frame.key
            
            if key1 is None:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            try:
                name = self.backbone.save(key1)
                if name is None:
                    self._status_set(f'Nothing to save yet!', 'red')
                    return
            except:
                self._status_set(f'Data Saving was unsuccessfull!', 'red')
                return
            else:
                self._status_set(f'Data Saving was successfull!\nName: {name}.', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Select Data To Save.")
        new_window.columnconfigure(0, weight=1)
        frame = RadioDataset(new_window, self.backbone.return_data_keys(), last_result=True)
        frame.grid(column=0, row=0, sticky='ew')
        tk.Button(new_window, text='Save', command=lambda: _get_1_key_and_show(frame, new_window)).grid(sticky='sew')
        

    def _show_table(self):
        def _get_1_key_and_show(frame, window):
            frame._get_values()
            window.destroy()
            # Now get the key (not from the variable attached to radio widgets).
            key1= frame.key
            all_rows = not frame.yes_to_head
            if key1 is None:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            try:
                df = self.backbone.get_dataframe(key1, all=all_rows)
            except:
                self._status_set(f'Data Fetch was unsuccessfull!', 'red')
                return
            else:
                self._status_set(f'Data Fetch was successfull!\nData: {key1}.', 'green')

            # Time to show the data table.
            dTDa1 = tk.Toplevel(self)
            dTDa1.title(key1)
            dTDaPT = pdt.Table(dTDa1, dataframe=df, showtoolbar=True, showstatusbar=True, editable=bool(PARAMS['edit_table_at_show_time']))
            dTDaPT.show()
            dTDaPT.showIndex()
            

        new_window = tk.Toplevel(self)
        new_window.title("Select Data To Show.")
        new_window.columnconfigure(0, weight=1)
        frame = RadioDataset(new_window, self.backbone.return_data_keys(), only_head=True)
        frame.grid(column=0, row=0, sticky='ew')
        tk.Button(new_window, text='Show', command=lambda: _get_1_key_and_show(frame, new_window)).grid(sticky='sew')


    def _remove(self):
        def _get_keys_and_close(frame, window):
            frame._get_values()
            window.destroy()
            # Now get the keys (not from the variables attached to widgets).
            keys = frame.selected_keys

            if keys is None or keys == []:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            try:
                self.backbone.remove(keys)
            except:
                self._status_set(f'Removing was unsuccessfull!', 'red')
            else:
                self._status_set(f'Remove was successfull!\nRemoved: {keys}.', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Select Data To Remove.")
        new_window.columnconfigure(0, weight=1)
        frame = CheckBoxDataset(new_window, self.backbone.return_data_keys()) # Get only energy data-type entries.
        frame.grid(column=0, row=0, sticky='we')

        tk.Button(new_window, text='Remove', command=lambda: _get_keys_and_close(frame, new_window)).grid(sticky='sew')
        

    def _group(self):
        def _get_keys_and_close(frame, window):
            frame._get_values()
            window.destroy()
            # Now get the keys (not from the variables attached to widgets).
            keys = frame.selected_keys
            nm = frame.name
            if keys is None or keys == []:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            try:
                name = self.backbone.group(keys, nm)
            except InvalidSelectedDataException:
                self._status_set(f'Concatenation was unsuccessfull!\nInvalid Selected Data\n(common index)', 'red')
            except:
                self._status_set(f'Grouping was unsuccessfull!', 'red')
            else:
                self._status_set(f'Grouping was successfull!\nCombined {keys}.\nName: {name}.', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Select Data For Grouping.")
        new_window.columnconfigure(0, weight=1)
        frame = CheckBoxDataset(new_window, self.backbone.return_data_keys('energy_data'), name_field=True) # Get only energy data-type entries.
        frame.grid(column=0, row=0, sticky='we')

        tk.Button(new_window, text='Group', command=lambda: _get_keys_and_close(frame, new_window)).grid(sticky='sew')
        
    def _resample(self):
        def _get_keys_and_close(frame, window):
            def _get_resample_period(frame2, window):
                frame2._get_values()
                window.destroy()
                if frame2.period is None:
                    self._status_set('No Period Selected!', 'red')
                    return
                try:
                    keys_many = self.backbone.resample(keys, period = frame2.period)
                except Exception as e:
                    print(e) # Print error on terminal.
                    self._status_set('Error While Resampling Data!', 'red')
                else:
                    self._status_set('Resampling Was Sucessfull!\nKeys: {keys_many}', 'green')

            frame._get_values()
            window.destroy()
            # Now get the keys (not from the variables attached to widgets).
            keys = frame.selected_keys
            if keys == []: return
            new_window = tk.Toplevel(self)
            new_window.title("Select Data For Resampling.")
            new_window.columnconfigure(0, weight=1)
            frame2 = SelectSamplePeriod(new_window, optional_period=False)
            frame2.grid(column=0, row=0, sticky='we')
            tk.Button(new_window, text='Set Resample Period', command=lambda: _get_resample_period(frame2, new_window)).grid(sticky='sew')

        new_window = tk.Toplevel(self)
        new_window.title("Select Data For Resampling.")
        new_window.columnconfigure(0, weight=1)
        frame = CheckBoxDataset(new_window, self.backbone.return_data_keys('energy_data'), name_field=False) # Get only energy data-type entries.
        frame.grid(column=0, row=0, sticky='we')

        tk.Button(new_window, text='Select', command=lambda: _get_keys_and_close(frame, new_window)).grid(sticky='sew')
        

    def _show_loaded_data(self):
        self._status_set('Show Data button was pressed.', 'grey')

        new_window = tk.Toplevel(self)
        new_window.title("Data Stored In Program")
        new_window.columnconfigure(0, weight=1)
        new_window.rowconfigure(0, weight=2)
        tk.Label(new_window, text='The data in program\'s memory are the following:', anchor='w').grid(row=0,sticky='ew',pady=5)
        saved_data_keys = self.backbone.return_data_keys()
        for i, key in enumerate(saved_data_keys, start=1):
            tk.Label(new_window, text=key, anchor='w').grid(sticky='ew')
            new_window.rowconfigure(i, weight=1)

    def _concat(self):
        def _get_2_keys_and_close(frame1, frame2, window, nm=None):
            frame1._get_values()
            frame2._get_values()
            window.destroy()
            # Now get the keys (not from the variables attached to widgets).
            key1, key2 = frame1.key, frame2.key
            if key1 is None or key2 is None or key1 == key2:
                self._status_set(f'Dataset selection was unsuccessfull', 'red')
                return
            try:
                name = self.backbone.concatenate(key1, key2, parse_name(nm))
            except SameClassException:
                self._status_set(f'Concatenation was unsuccessfull!\nDataframes should have same columns.', 'red')
            except:
                self._status_set(f'Concatenation was unsuccessfull!', 'red')
            else:
                self._status_set(f'Concatenation was successfull!\nCombined {key1} with {key2}\nName: {name}.', 'green')

        new_window = tk.Toplevel(self)
        new_window.title("Select Data To Concatenate With.")
        new_window.columnconfigure(0, weight=1)
        new_window.columnconfigure(1, weight=1)
        frame1 = RadioDataset(new_window, self.backbone.return_data_keys())
        frame1.grid(column=0, row=0, sticky='ew')
        frame2 = RadioDataset(new_window, self.backbone.return_data_keys())
        frame2.grid(column=1, row=0, sticky='ew')
        name_var = tk.StringVar(value='')
        tk.Label(new_window, text='Name for the new data (optional):').grid(columnspan=2, sticky='we')
        tk.Entry(new_window,textvariable=name_var, justify='center').grid(columnspan=2, sticky='we')
        tk.Button(new_window, text='Apply', command=lambda: _get_2_keys_and_close(frame1, frame2, new_window, name_var.get())).grid(columnspan=2, sticky='sew')
        

    def _status_set(self, message, color):
        # self.resizable(False,True)
        self.status_variable.set(message)
        self.status.config(bg=color)
    
    def _reset_status(self, event):
        self.status_variable.set('')
        defaultbg = self.cget('bg')
        self.status.config(bg=defaultbg)

    def _help_message(self):
        self._status_set('Help button was pressed.', 'grey')
        new_window = tk.Toplevel(self)
        new_window.title("Help")
        new_window.columnconfigure(0, weight=0)
        new_window.columnconfigure(1, weight=1)
        tk.Label(new_window, text="This program is used to perform analysis of energy data.\nIt was developed by Alexandros Barmperis under the guidelines provided by Vassilios Barberis.", anchor='w').grid(column=0, columnspan=2, row=0, sticky='we')

        for i, tup in enumerate(self.backbone.get_help_list_of_tuples(), start=1):
            tk.Label(new_window, text=tup[0], anchor='w').grid(column=0, row=i, sticky='w')
            tk.Label(new_window, text=tup[1], anchor='w', justify='left').grid(column=1, row=i, sticky='w')

    def _load_data(self):
        def _select_data(frame, window):
            frame._get_values()
            window.destroy()
            # Pop up window to select the file.
            fn_tuple = filedialog.askopenfilenames(title='Choose files.')
            if fn_tuple == '':
                self._status_set('No Data Selected!', 'grey')
                return
            try:
                self.backbone.load_data_from_fn_paths(fn_tuple, frame.period)
            except Exception as e:
                print(e) # Print error on terminal.
                self._status_set('Error While Loading Data!', 'red')
            else:
                self._status_set('Data Loaded Sucessfully!', 'green')
            
        new_window = tk.Toplevel(self)
        new_window.title("Select Sampling Period")
        new_window.columnconfigure(0, weight=1)
        frame = SelectSamplePeriod(new_window, txt='Sample Frequency', name_field=False)
        frame.grid(sticky='ew')
        tk.Button(new_window, text='Select Data', command=lambda: _select_data(frame, new_window)).grid(sticky='ew')
        
        
        

        

# Create root window
class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.grid_propagate(0)
        # root.geometry('200x150')
        self.title('Energy Analyst')
        # tk.Label(self, text='Please fill the form').grid()
        backbone = Functionality()
        MainFrame(self, backbone).grid(sticky='nsew') # Pass parent to main frame.
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        

  
class ScrollableFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        # create a canvas object and a vertical scrollbar for scrolling it
        self.vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.vscrollbar.pack(side='right', fill="y",  expand="false")
        self.canvas = tk.Canvas(self,
                                bg='#444444', bd=0,
                                height=350,
                                highlightthickness=0,
                                yscrollcommand=self.vscrollbar.set)
        self.canvas.pack(side="left", fill="both", expand="true")
        self.vscrollbar.config(command=self.canvas.yview)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = tk.Frame(self.canvas, **kwargs)
        self.canvas.create_window(0, 0, window=self.interior, anchor="nw")

        self.bind('<Configure>', self.set_scrollregion)


    def set_scrollregion(self, event=None):
        """ Set the scroll region on the canvas"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        

if __name__ == '__main__':
    gui = Application()
    gui.mainloop()