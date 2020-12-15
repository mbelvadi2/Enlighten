# Enlighten

This python script is intended for customers of the solar panel equipment company, Enphase, who wish to use their Enlighten API accounts to harvest usage reports from their equipment.

You can either run the python directly, or if you have Windows 10, you can download the pre-compiled executable.
There is nothing to install with that - you just create a folder to put it in, and put it there and run it directly.

There is some configuration you need to do with Enphase before you can use this application, read the details at:
https://developer.enphase.com/docs/quickstart.html

Then once you have all your credentials in place, you need to create an enlighten.ini file and put it wherever you have either the python code or the Windows 10 executable.
Note that the first line of the ini tells the program where to save the generated reports.

The ini file is a simple plain text file with four "variables" separated from their values with a single space (remove all the comments below!):
--------<br/>
reportfolder  blahblah    #  a relative path from wherever the executable is - even on Windows, use forward slashes not backslashes<br/>
account ######   # your enphase account #<br/>
user_id blahblah  # find this in the enlighten web app under Account - API settings<br/>
key blahblah   # this is the api key from the developer quickstart instructions<br/>
--------<br/>
This is mostly just something I wrote for myself and decided to try sharing with the world here on Github.
It only supports the kinds of reports that are relevant to me, a residential Enphase customer, but the code is very simple, so if some of those other reports (eg the "revenue-grade" ones) would be useful to you, just let me know or if you know python I'd be happy to let you contribute to this project.
