import requests

headers = {"X-Yandex-API-Key": 'fe52aeef-8626-45e1-81ad-720a8e098774'}


#  API Yandex.Погода "Тестовый"


def get_coords(toponym_to_find):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym_to_find,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if response:
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        return toponym_coodrinates.split(" ")
    else:
        return None, None


def weather_response(place):
    if len(place) == 2:
        coords = place
    else:
        coords = get_coords(place)
    weather_api_server = 'https://api.weather.yandex.ru/v1/forecast?'
    weather_params = {
        "lon": float(coords[0]),
        "lat": float(coords[1]),
        "lang": "ru_RU"
    }
    response = requests.get(weather_api_server, weather_params, headers=headers)
    return response.json()


def current_weather(response):
    city = response["info"]["tzinfo"]["name"].split('/')[-1]
    date = response["now_dt"][:10]
    offset = response["info"]["tzinfo"]["offset"] // 3600
    time = response["now_dt"][11:16]
    h, m = map(int, time.split(':'))
    time = f'{h + offset}:{m:02}'
    fact = response["fact"]
    temp = fact["temp"]
    condition = fact["condition"]
    wind_dir = fact["wind_dir"]
    wind_speed = fact["wind_speed"]
    pressure = fact["pressure_mm"]
    humidity = fact["humidity"]
    return f'Current weather in {city} today {date} at time {time}:\n' \
           f'Temperature: {temp},\n' \
           f'Pressure: {pressure} mm,\n' \
           f'Humidity: {humidity}%,\n' \
           f'{condition},\n' \
           f'Wind {wind_dir}, {wind_speed} m/s.'


def forecast_weather(response, days):
    city = response["info"]["tzinfo"]["name"].split('/')[-1]
    forecasts = response["forecasts"]
    result = []
    for forecast in forecasts[1:days + 1]:
        date = forecast["date"]
        temp = forecast["parts"]["day"]["temp_avg"]
        condition = forecast["parts"]["day"]["condition"]
        wind_dir = forecast["parts"]["day"]["wind_dir"]
        wind_speed = forecast["parts"]["day"]["wind_speed"]
        pressure = forecast["parts"]["day"]["pressure_mm"]
        humidity = forecast["parts"]["day"]["humidity"]
        result.append(f'Weather forecast in {city} for {date}:\n'
                      f'Temperature: {temp},\n'
                      f'Pressure: {pressure} mm,\n'
                      f'Humidity: {humidity}%,\n'
                      f'{condition},\n'
                      f'Wind {wind_dir}, {wind_speed} m/s.')
    return '\n\n'.join(result)
