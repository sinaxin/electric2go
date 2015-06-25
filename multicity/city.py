#!/usr/bin/env python2
# coding=utf-8


CITIES = {
    'berlin': {
        'of_interest': True
    }
}


# from https://www.multicity-carsharing.de/en/
# needs additional requests per car to get fuel/charge, address
# rather horrible, unless I can find a better API


# fill in city data that can be assumed and autogenerated
for city, city_data in CITIES.items():
    if 'API_AVAILABLE_VEHICLES_URL' not in city_data:
        city_data['API_AVAILABLE_VEHICLES_URL'] = 'https://kunden.multicity-carsharing.de/kundenbuchung/hal2ajax_process.php?searchmode=buchanfrage&lat=52.51&lng=13.39&instant_access=J&open_end=J&ajxmod=hal2map&callee=getMarker'
