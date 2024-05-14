# Import necessary libraries
import streamlit as st
import requests
import datetime
import google.generativeai as genai
from google.api_core import retry
import pandas as pd
import plotly.graph_objects as go
from streamlit_folium import folium_static
import folium



st.set_page_config(page_title="☁️ Weather App")

# For convenience, a simple wrapper to let the SDK handle error retries
def generate_with_retry(model, prompt, max_words):
  prompt_words = prompt.split()

  truncated_prompt = ' '.join(prompt_words[:max_words])

  return model.generate_content(truncated_prompt, request_options={'retry':retry.Retry()})

# Function to get weather Data from OpenWeathermap API
def get_city_data(city, accuweather_API_key):
    base_url = 'http://dataservice.accuweather.com/locations/v1/cities/search'
     # Parameters including API key and city name
    params = {
        "apikey": accuweather_API_key,
        "q": city
    }
    #complete_url = base_url + 'q=' + city +  '&appid=' + weather_API_key 
    response = requests.get(base_url, params = params)
    return response.json()


def get_weather_data(Location_Key, accuweather_API_key):
    base_url = f'http://dataservice.accuweather.com/currentconditions/v1/{Location_Key}'
    params = {
        'apikey': accuweather_API_key,
        'details': True
    }
    #complete_url = base_url + 'q=' + city +  '&appid=' + weather_API_key 
    response = requests.get(base_url, params = params)
    return response.json()

# Function for generating weather description using OpenAI's GPT Model
def generate_weather_description(data, gemini_API_key):
    #openai.api_key = openai_API_key
    google_api_key = genai.configure(api_key=gemini_API_key)

    try:
        # Converting temperature from Kelvin to Celsius
        temp = data[0]['Temperature']['Metric']['Value'] 
        desc = data[0]['WeatherText']
        uv = data[0]['UVIndexText']
        prompt = f'The current weather in city is {desc} with a temperature of {temp: .1f} °C and UV Index {uv}. Do not tell what temperature is or what description means. Do not just focus on the description also focus on temperature, pressure and humidity. Just Explain what to do in this weather and temperature in a simple way for general audience.'
        model = genai.GenerativeModel('gemini-pro')
        response = generate_with_retry(model, prompt, 50).text

        return response
    
    except Exception as e:
        return str(e)


def get_weekly_forecast(accuweather_API_key, Location_Key):
    base_url = f'http://dataservice.accuweather.com/forecasts/v1/daily/5day/{Location_Key}'
    params = {
        'apikey': accuweather_API_key,
        'details': True,
        'metric': True
    }
    #base_url = 'https://api.openweathermap.org/data/2.5/forecast/daily?'
    #complete_url = f"{base_url}lat={lat}&lon={lon}&cnt=7&appid={weather_API_key}"
    response = requests.get(base_url, params = params)
    return response.json()


def display_weekly_forecast(data):
    try:
        st.write('==================================================================================')
        #st.write('Weekly Weather Forecast')
        #displayed_dates = set() # To keep track of dates for which forecast has been displayed

        # Extract relevant information from the forecast data
        forecast_list = data['DailyForecasts']
        #print(forecast_list)
        forecast_entries = []
        for entry in forecast_list:
            date = pd.to_datetime(entry['Date']).strftime('%A, %B %d')  # Convert timestamp to datetime
            min_temp = str(entry['Temperature']['Minimum']['Value']) + '°C'
            max_temp = str(entry['Temperature']['Maximum']['Value']) + '°C'  
            weather = entry['Day']['IconPhrase']
            rain_prob = str(entry['Day']['RainProbability']) + '%'
            forecast_entries.append({'Date': date, 'Weather': weather, 'Min Temperature': min_temp, 'Max Temperature': max_temp, 'Rain Probability': rain_prob})

        # Create DataFrame from extracted information
            #forecast_entries.append({'Date':date, 'Min temp': min_temp, 'Max temp': max_temp})
        #st.write(forecast_entries)
        forecast_df = pd.DataFrame(forecast_entries)
        #print(forecast_df)
        return forecast_df
    
    except Exception as e:
        st.error('Error in displaying weekly forecast: ' + str(e))




def main():
    
    # Sidebar Configuration
    st.sidebar.image('clipart1294094.png', width = 120)
    st.sidebar.title('Weather Forecasting using LLM')
    city = st.sidebar.text_input('Enter City Name', ' ')

    #API Keys
    accuweather_API_key = ' Use your API Key Here ' # You will get it from logging into your account in OpenWeathermap

    gemini_API_key = ' Give Your own gemini_API key'
    # Button to fetch and display weather data
    submit = st.sidebar.button('Get Weather')
    

    if submit:

        city_data = get_city_data(city, accuweather_API_key)
        Location_Key = city_data[0]['Key']
        lat = city_data[0]['GeoPosition']['Latitude']
        lon = city_data[0]['GeoPosition']['Longitude']

        #weather = get_weather_data(Location_Key,accuweather_API_key)
        #print('This is the current weather details:\n', weather)
        st.header(':orange[Weather updates for the city ' + city + ' is:]')
        with st.spinner('Fetching weather data...... ⌛'):
            weather_data = get_weather_data(Location_Key, accuweather_API_key)
            print('The weather is following:\n\n:', weather_data)


            # Check if the city is found and weather data is displayed
            if weather_data[0].get('cod') != 404:
                col1,col2 = st.columns(2)
                with col1:
                    st.metric('Temperature 🌡', f"{weather_data[0]['Temperature']['Metric']['Value']: .1f} °C")
                    st.metric('Min  | Max', f"{weather_data[0]['TemperatureSummary']['Past6HourRange']['Minimum']['Metric']['Value']: .1f} °C | {weather_data[0]['TemperatureSummary']['Past6HourRange']['Maximum']['Metric']['Value']: .1f} °C")
                    st.metric('Feels like 🌡️', f"{weather_data[0]['RealFeelTemperature']['Metric']['Value']: .1f} °C")
                    if weather_data[0]['RelativeHumidity'] > 70:
                        st.metric('Humidity 💧 🥵', f"{weather_data[0]['RelativeHumidity']}%")
                    elif weather_data[0]['RelativeHumidity'] in [40, 70]:
                        st.metric('Humidity 💧 :sweat:', f"{weather_data[0]['RelativeHumidity']}%")
                    else:
                        st.metric('Humidity 💧 :relieved:', f"{weather_data[0]['RelativeHumidity']}%")
                with col2:
                    st.metric('Pressure', f"{weather_data[0]['Pressure']['Metric']['Value']} mb")
                    st.metric('Wind Speed 🌫🍃(Direction)', f"{weather_data[0]['Wind']['Speed']['Metric']['Value']} km/h({weather_data[0]['Wind']['Direction']['Degrees']}°{weather_data[0]['Wind']['Direction']['Localized']})")
                    if 'partly' in weather_data[0]['WeatherText'].lower():
                        st.metric('Sky :barely_sunny:', f"{weather_data[0]['WeatherText']}")
                    elif 'shower' in weather_data[0]['WeatherText'].lower():
                        st.metric('Sky :umbrella_with_rain_drops:', f"{weather_data[0]['WeatherText']}")
                    elif 'thunderstorm' in weather_data[0]['WeatherText'].lower():
                        st.metric('Sky :rain_cloud::lightning:', f"{weather_data[0]['WeatherText']}")
                    elif 'rain' in weather_data[0]['WeatherText'].lower():
                        st.metric('Sky :rain_cloud:', f"{weather_data[0]['WeatherText']}")
                    elif 'cloud' in weather_data[0]['WeatherText'].lower():
                        st.metric('Sky ☁️', f"{weather_data[0]['WeatherText']}")
                    else:
                        st.metric('Sky ☀️', f"{weather_data[0]['WeatherText']}")

                    
                    if weather_data[0]['UVIndexText'] == 'Low':
                        st.metric('UV Index 🔆⬇', f'{weather_data[0]['UVIndex']}')
                    elif weather_data[0]['UVIndexText'] == 'High':
                        st.metric('UV Index 🔆⬆', f'{weather_data[0]['UVIndex']}')
                    else:
                        st.metric('UV Index 🔆⬆⬆', f'{weather_data[0]['UVIndex']}')


                # Generate and display a friendly weather description
                st.header(':orange[Some Pros & Cons you should take in this weather]', divider='blue')
                weather_description = generate_weather_description(weather_data, gemini_API_key)
                st.write(weather_description)

                # Call function to get weekly forecast
                st.header(':orange[5 days Weather Forecast]', divider='rainbow')
                forecast_data = get_weekly_forecast(accuweather_API_key, Location_Key)

                # Extract relevant information from the forecast data
                forecast_list = forecast_data['DailyForecasts']
                print(forecast_list)
                forecast_entries = []
                for entry in forecast_list:
                    date = pd.to_datetime(entry['Date']).strftime('%A, %B %d')  # Convert timestamp to datetime
                    min_temp = entry['Temperature']['Minimum']['Value'] 
                    max_temp = entry['Temperature']['Maximum']['Value']  
                    weather = entry['Day']['IconPhrase']
                    forecast_entries.append({'Date': date, 'Min Temperature (°C)': min_temp, 'Max Temperature (°C)': max_temp, 'Weather': weather})

                # Create DataFrame from extracted information
                    #forecast_entries.append({'Date':date, 'Min temp': min_temp, 'Max temp': max_temp})
                #st.write(forecast_entries)
                forecast_df = pd.DataFrame(forecast_entries)
                print(forecast_df)

                # Calculate y-axis range based on temperature data
                min_temp = forecast_df['Max Temperature (°C)'].min() - 1
                max_temp = forecast_df['Max Temperature (°C)'].max() + 1
                y_range = [min_temp , max_temp]

                # Plotly figure
                fig = go.Figure()

                # Add trace for max temperature
                fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Max Temperature (°C)'],
                                        mode='lines',
                                        name='Max Temperature (°C)',
                                        line=dict(color='red', width=1)))
                
                # Annotate max temperature for every day forecast
                for i, row in forecast_df.iterrows():
                    if not pd.isna(row['Max Temperature (°C)']):  # Annotate every 6th data point (corresponding to 6-hour intervals)
                        fig.add_annotation(x=row['Date'], y=row['Max Temperature (°C)'],
                                           text=f"{row['Max Temperature (°C)']:.1f} °C",
                                           showarrow=False)

                # Update layout
                fig.update_layout(title='5 days Maximum Temperature Forecast',
                                xaxis_title='Date',
                                yaxis_title='Temperature (°C)',
                                xaxis=dict(tickformat='%b %d'),  # Format to display only month and day
                                yaxis=dict(range=y_range),  # Disable zooming on y-axis
                                plot_bgcolor='rgba(0,0,0,0)',  # Set transparent background
                                hovermode='x',  # Show hover information only along x-axis
                                )

                # Show plot
                st.plotly_chart(fig)

                if forecast_data.get('cod') != "404":
                    st.dataframe(display_weekly_forecast(forecast_data))
                    

                else:
                    st.error('Error fetching weekly forecast data!')

                m = folium.Map(location = [lat, lon])
                folium.Marker([lat,lon], 
                              popup = city,
                              tooltip = f"{city}\n{weather_data[0]['TemperatureSummary']['Past6HourRange']['Minimum']['Metric']['Value']: .1f} °C | {weather_data[0]['TemperatureSummary']['Past6HourRange']['Maximum']['Metric']['Value']: .1f} °C"
                              ).add_to(m)
                
                folium_static(m,width = 700,height = 300)
                



            else:
                # Display an error message if the city is not found 
                st.error('City not found or an error occurred!')






if __name__ == '__main__':
   main()


