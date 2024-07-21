import pandas as pd


def get_weather_data(bounding_box):
    weather_data = pd.read_csv('../data/WeatherDataMonthly.csv')
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    filtered_data = weather_data[
        (weather_data['Lon_DD'] >= bounding_box[0]) & 
        (weather_data['Lon_DD'] <= bounding_box[2]) & 
        (weather_data['Lat_DD'] >= bounding_box[1]) & 
        (weather_data['Lat_DD'] <= bounding_box[3])
    ]

    temp_data = []
    precip_data = []
    # each month is
    for i in range(0,12):
        month = {
            'monthIdx': i,
            'mean': filtered_data['Mean_' + months[i] + '_Temp'].mean(),
            'low': filtered_data['Mean_Low_' + months[i] + '_Temp'].mean(),
            'high': filtered_data['Mean_High_' + months[i] + '_Temp'].mean()
        }
        temp_data.append(month)
        month = {
            'monthIdx': i,
            'mean': filtered_data['Mean_' + months[i] + '_Precip'].mean(),
            'min': filtered_data['Min_' + months[i] + '_Precip'].mean(),
            'max': filtered_data['Max_' + months[i] + '_Precip'].mean()
        }
        precip_data.append(month)

    return temp_data, precip_data