[![PyPI](https://img.shields.io/static/v1?label=pandas&message=1.5&color=blue)](https://pandas.pydata.org/)
[![PyPI](https://img.shields.io/static/v1?label=numpy&message=1.24&color=green)](https://numpy.org/)
[![PyPI](https://img.shields.io/static/v1?label=Tcl/Tk&message=8.5&color=green)](https://docs.python.org/3/library/tkinter.html)



# Energy-Analyst

Energy Analyst is a PC application designed to aid the ad hoc analysis of energy data. The range and specifications of the data transformations are aligned with the requirements specified by the ISO50001:2011 protocol regarding energy management. The target audience of this application is small businesses and freelancers wishing to perform specialized (for the task) queries on energy data.

## Installation
* Downloaad this repository and unzip the contents.
* Move into the directory of the folder you just unziped.
* Open a terminal on the a system with python 3 installed and run `pip install -r requirements.txt` (alternatively, create a virtual environment)
* Run `python3 gui.py`

## Data Format
Check the sample.xlsx for a sample of the prefered data format.
Note that the time interval of the energy data dose not have to be hourly.<br />
In general, the input data can be in either .csv or .xlsx form and they must have two columns:
- The first one should be a valid datetime index.
- The second column should be the energy consumed untill this time (in kW).<br />

[Deddie](https://deddie.gr/) data follow this format.

## Scope
Energy Analyst is developed to aid the ad hoc analysis of energy data, a requirement for energy management of office buildings and hotels. This facilitation is in the form of a friendly interface that encloses pre-defined, common queries and transformations so that the user will not have to repeatedly formulate and perform those intricate and time-consuming data workflows. In other words, this application aims in reducing the overall time that ad hoc energy data analysis takes up.

## Files
* `gui.py` <br/>
This is the python file that includes the classes for the graphical user interface.
* `functionality.py` <br />
Includes callback functions which make the buttons of the gui functional.
* `utils.py` <br />
Encloses various utility functions that are called throughout the program.
* `data_analysis.py` <br />
The back-bone of the program. All the queries and all the data operations are perforemed by classes defined in this file.
* `params.json` <br />
Parameters that the user can easily change providing even more flexibility. The parameters are self explanatory. Some of those specify how to handle missing values, whether or not <it>0</it> numbers represent missing data. Other parameters concern the office working hours, the calendar (by which national holidays are found) and the format of the input data.

## Range of Functionality
The application includes a `help` button which reveals the wide range of possible commands and their combinations.
![Help](https://github.com/abarmper/Energy-Analyst/blob/main/help.png)

## Screenshots
![Main Menu](https://github.com/abarmper/Energy-Analyst/blob/main/Main_menu.png)
![Date Selection](https://github.com/abarmper/Energy-Analyst/blob/main/Date_range.png)
![Energy Statistics](https://github.com/abarmper/Energy-Analyst/blob/main/Energy_Stats_part.png)
![Show Table](https://github.com/abarmper/Energy-Analyst/blob/main/Table_show.png)

