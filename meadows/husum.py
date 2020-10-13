import requests
import numpy as np

# Polynomial Transform from Underwood to Husum, determined using husum-gauge repo
husum_height_function= np.poly1d([0.04779491, -0.8810747, 6.72749403, -13.449101395])

def get_husum_height():
    underwood_height = get_underwood_height()[1]
    if underwood_height is not None:
        print(underwood_height)
        husum_height = np.polyval(husum_height_function, underwood_height)
        return round(husum_height, 2)
    return None


def get_underwood_height():
    usgs_base_url = 'http://waterservices.usgs.gov/nwis/iv/?site=14123500&format=json'
    request_string = usgs_base_url 
    r = requests.get(request_string)
    if r.status_code ==200:
        usgs_json = r.json()['value']['timeSeries']
        for data_series in usgs_json:
            if data_series['variable']['variableCode'][0]['value'] == '00060':
                usgs_cfs = float(data_series['values'][0]['value'][0]['value'])
            elif data_series['variable']['variableCode'][0]['value'] == '00065':
                usgs_height_ft = float(data_series['values'][0]['value'][0]['value'])

        return([usgs_cfs,usgs_height_ft])
    return None

if __name__ == '__main__':
    print(get_husum_height())