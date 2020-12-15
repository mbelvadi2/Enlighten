"""
To use this app, you need to first register, get your API key, and associate that key with this app and user_id.
Instructions for getting all that configured are:
https://developer.enphase.com/docs/quickstart.html

Once that's done, you need to create the enlighten.ini file with the appropriate values.

enlighten.ini is a plain text file with 4 variables stored one per line with a space between the variable name and value:
reportfolder  #  a relative path from wherever the executable is - even on Windows, use forward slashes not backslashes
account ######
user_id blahblah  - find this in the enlighten web app under Account - API settings
key blahblah   - this is the api key
Make sure your user id gives permission to this app
enwh = energy consumed or produced by microinverters during this interval, measured in Watt hours.
powr = average power produced by microinverters during this interval, measured in Watts.

Compiling the executable:
pip install pyinstaller
pip install -r requirements.txt   # in the project directory
pip show validators  # copy the package location path
pyi-makespec --paths=DirectoryWithValidatorsPackage main.py
pyinstaller --noconsole --onefile main.py -n "EnlightenReport"
Find the EnlightenReport.exe in the dist folder - you can then move it anywhere and run it directly - no "install"

"""
from pathlib import Path
import os.path
import requests
import json
from tkinter import *
from tkinter import messagebox as mb
from tkinter import Label as tkLabel
from tkinter.ttk import *
from tkcalendar import *
import datetime
import logging
# from babel.numbers import *

from pandas import json_normalize

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'

init_file = 'enlighten.ini'

def get_data(buildurl):
    r = requests.get(buildurl, headers={"User-Agent": USER_AGENT})
    data = json.loads(r.text)
    if 'reason' in str(data):
        print(f'Error in response from Enlighten, invalid date for type of data:\n{str(data)}')
        return None
    else:
        return data


if __name__ == '__main__':
    loggerfile = 'errorlog-enlighten.txt'
    infologger = logging.getLogger()
    infologger.setLevel(logging.ERROR)  # DEBUG is the lowest, includes all
    infohandler = logging.FileHandler(loggerfile, 'w', 'utf-8')
    infoformatter = logging.Formatter('%(asctime)s\t%(message)s')
    infohandler.setFormatter(infoformatter)  # Pass handler as a parameter, not assign
    infologger.addHandler(infohandler)
    settings_dict = {}
    try:
        settings_file = open(init_file, 'r')
    except:
        print(f"Unable to open settings file {init_file}, exiting.")
        infologger.exception(f"Unable to open settings file {init_file}")
        _ = input('Press Enter to exit program now')
        exit(-1)
    else:
        for setting in settings_file:
            key, value = setting.split(' ')
            settings_dict[key] = value.rstrip()
        if not settings_dict['reportfolder'] or not settings_dict['account'] or not settings_dict["key"] or not settings_dict["user_id"]:
            print(f"Missing one of the critical settings in {init_file}: reportfolder, account, key, user_id:  exiting.")
            exit(-1)
    try:
        recordsfolder = Path(settings_dict['reportfolder'])
        os.chdir(recordsfolder)
    except:
        recordsfolder = Path('.')
        infologger.exception(f"Unable to open settings file {settings_dict['reportfolder']}")

    basekey = f'https://api.enphaseenergy.com/api/v2/systems/{settings_dict["account"]}/'
    credentials = f'key={settings_dict["key"]}&user_id={settings_dict["user_id"]}&datetime_format=iso8601'
    while True:
        df = {}
        df_all = {}
        dfsub = {}
        window = Tk()
        window.title("Select Enlighten report options")
        # window.geometry('375x500')
        report_lbl_top = tkLabel(text="Report Type: ")
        report_lbl_top.grid(column=0, row=0, sticky='W', padx=(15,1))
        report_lbl = tkLabel(text="Report type not yet saved", fg="red")
        report_lbl.grid(column=0, row=2, sticky='W', padx=(15,1))

        report_type = StringVar()
        combo = Combobox(window, textvariable=report_type)
        combo['values'] = ('Select from list', 'summary', 'stats', 'energy_lifetime', 'consumption_stats')
        combo.current(0)  # set the selected item
        combo.grid(column=0, row=1, sticky='W', padx=(15,1))
        def report_clicked():
            global report_type
            report_type = combo.get()
            report_lbl.config(text=f'Selected report: {report_type}', fg="green")
            if str(report_type) == 'stats':
                mb.showwarning(title='WARNING',message='For stats report\nchoose at most a single 24-hour period!')
        report_btn = Button(window, text="Save report type",command=report_clicked)
        report_btn.grid(column=1, row=1, sticky='W')

        cal_lbl_top = tkLabel(text="Select Start and End Dates\nClick date in grid first then appropriate select button ")
        cal_lbl_top.grid(column=0, row=3,  columnspan=2, pady=(20,5))
        try:
            cal = Calendar(window, selectmode="day", date_pattern="y-mm-dd", year=2020, month=12, day=12)
        except:
            infologger.exception(f"Unable to open calendar widget")
            exit(-1)
        else:
            cal.grid(column=0, row=5, columnspan=2, padx=(15,15))

        def start_get_date():
            global start_date
            start_date = cal.get_date()
            start_label.config(text=f'Start date: {start_date}', fg="green")
        def end_get_date():
            global end_date
            end_date = cal.get_date()
            end_label.config(text=f'End date: {end_date}', fg="green")

        start_date = StringVar()
        end_date = StringVar()

        start_button = Button(window, text="Select Start Date", command=start_get_date)
        start_button.grid(column=0, row=6, sticky='W', padx=(15,1))
        start_label = tkLabel(window, text='Start Date not selected', fg="red")
        start_label.grid(column=0,row=8, sticky='W', padx=(15,1))



        end_button = Button(window, text="Select End Date", command=end_get_date)
        end_button.grid(column=1, row=6, sticky='W')
        end_label = tkLabel(window, text='End Date not selected', fg="red")
        end_label.grid(column=1, row=8, sticky='W')

        starthour_top_label = tkLabel(window, text='Start Hour:')
        starthour_top_label.grid(column=0, row=10, sticky='W', padx=(15,1), pady=(20,5))
        start_hourdef = IntVar()
        start_hourdef.set(0)
        start_hourspin = Spinbox(window, from_=0, to=23, width=5, textvariable=start_hourdef)
        start_hourspin.grid(column=0, row=11, sticky='W', padx=(15,1))
        starthour_label = tkLabel(window, text='Start Hour not selected', fg="red")
        starthour_label.grid(column=0, row=12, sticky='W', padx=(15,1))
        def set_start_hour():
            global start_hourdef
            start_hourdef = start_hourspin.get()
            starthour_label.config(text=f'Start hour: {start_hourdef}', fg="green")

        start_hour_btn = Button(window, text="Save start time", command=set_start_hour)
        start_hour_btn.grid(column=0, row=13, sticky='W', padx=(15,1), pady=(1,15))

        endhour_top_label = tkLabel(window, text='End Hour:')
        endhour_top_label.grid(column=1, row=10, sticky='W', pady=(20,5))
        end_hourdef = IntVar()
        end_hourdef.set(23)
        end_hourspin = Spinbox(window, from_=0, to=23, width=5, textvariable=end_hourdef)
        end_hourspin.grid(column=1, row=11, sticky='W')
        endhour_label = tkLabel(window, text='End Hour not selected', fg="red")
        endhour_label.grid(column=1, row=12, sticky='W')
        def set_end_hour():
            global end_hourdef
            end_hourdef = end_hourspin.get()
            endhour_label.config(text=f'End hour: {end_hourdef}', fg="green")
        end_hour_btn = Button(window, text="Save end time", command=set_end_hour)
        end_hour_btn.grid(column=1, row=13, sticky='W', pady=(1,15))

        def submit_close():
            window.destroy()
        close_btn = Button(window, text="SUBMIT", command=submit_close)
        close_btn.grid(column=0, row=20, columnspan=2, pady=(10,15))

        window.mainloop()

        start_hourdef = start_hourdef.zfill(2)
        end_hourdef = end_hourdef.zfill(2)
        report_type = str(report_type)
        start_date = str(start_date)
        end_date = str(end_date)
        # print(f'Report type: {report_type}')
        # start_date_time = input('Start date/time in yyyy-mm-dd-hh format default is 2020-12-12-8: ')
        # if start_date_time == '':
        start_date_time = start_date + '-' + start_hourdef
        # print(f'Start date/time: {start_date_time}')
        start_year = int(start_date_time[0:4])
        start_month = int(start_date_time[5:7])
        start_day = int(start_date_time[8:10])
        start_hour = int(start_date_time[11:13])
        end_date_time = end_date + '-' + end_hourdef
        # print(f'End date/time: {end_date_time}')
        end_year = int(end_date_time[0:4])
        end_month = int(end_date_time[5:7])
        end_day = int(end_date_time[8:10])
        end_hour = int(end_date_time[11:13])
        epochstart = None
        epochend = None
        try:
            epochstart = str(datetime.datetime(start_year, start_month, start_day, start_hour, 0).timestamp())
        except:
            print('Invalid start date/time, exiting')
            exit(-1)
        try:
            epochend = str(datetime.datetime(end_year, end_month, end_day, end_hour, 0).timestamp())
        except:
            print('Invalid end date/time, exiting')
            exit(-1)
        other_args = f'&start_at={epochstart}&end_at={epochend}'

        if report_type == 'summary':
            other_args = ''
        # if report_type == 'energy_lifetime':
        #     other_args += '&production=all'

        buildurl = basekey + report_type + '?' + credentials + other_args
        # print(buildurl)
        data = get_data(buildurl)
        if data is None:
            exit(-1)
        if report_type == 'summary':
            df[report_type] = json_normalize(data)
            # print(df[report_type]['status'])
            df[report_type] = df[report_type].reindex(columns=['summary_date', 'status', 'energy_today', 'current_power'])
            # print(df[report_type])
            # print(df[report_type].columns)
            df[report_type].at[0, 'summary_date'] = df[report_type].at[0, 'summary_date'][0:10]
            # print(df[report_type].to_string(index=False))

        elif report_type == 'energy_lifetime':
            df_all[report_type] = json_normalize(data)
            dfsub[report_type] = df_all[report_type][['start_date', 'production']]
            df[report_type] = dfsub[report_type].copy()
            df[report_type]['start_date'] = df[report_type]['start_date'].apply(lambda x: str(x[0:10]))
            df[report_type]['total production'] = sum(df[report_type].loc[0,'production'])
            df[report_type] = df[report_type].drop(columns=['production'])
            # print(df[report_type].to_string(index=False))
        elif report_type == 'stats':
            df[report_type] = json_normalize(data['intervals'])
            df[report_type]['end_time'] = df[report_type]['end_at'].apply(lambda x: str(x[11:16]).replace('T', ' '))
            df[report_type]['end_date'] = df[report_type]['end_at'].apply(lambda x: str(x[0:10]).replace('T', ' '))
            df[report_type] = df[report_type].drop(columns=['end_at'])
            # print(df[report_type].to_string(index=False))
        elif report_type == 'consumption_stats':
            df_all[report_type] = json_normalize(data['intervals'])
            dfsub[report_type] = df_all[report_type][['end_at', 'enwh']]
            df[report_type] = dfsub[report_type].copy()
            df[report_type]['end_time'] = df[report_type]['end_at'].apply(lambda x: str(x[11:16]).replace('T', ' '))
            df[report_type]['end_date'] = df[report_type]['end_at'].apply(lambda x: str(x[0:10]).replace('T', ' '))
            df[report_type] = df[report_type].drop(columns=['end_at'])
            # print(df[report_type].to_string(index=False))

        df[report_type].to_csv(f'{report_type}_{start_date_time}_to_{end_date_time}.csv', index=False)

        window2 = Tk()
        window2.title("Do another report?")
        window2.geometry('375x500')
        exit_top_label = tkLabel(window2, text='Your request has been completed and report saved.\nQuit or do another report (click button to choose):')
        exit_top_label.grid(column=0, row=0, sticky='W', pady=(20, 5))
        def ExitApplication():
            MsgBox = mb.askquestion('Do more or exit', 'Request another report?', icon='warning')
            if MsgBox == 'no':
                window2.destroy()
                exit(0)
            else:
                window2.destroy()
        exit_button1 = Button(window2, text='Do another report?', command=ExitApplication)
        exit_button1.grid(column=0, row=2, sticky='W', pady=(1,15))

        window2.mainloop()


