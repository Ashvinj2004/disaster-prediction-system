"""
Raspberry Pi Weather Station with Disaster Prediction
=====================================================

Reads local sensor data (temperature, humidity, light) and combines it with
external OpenWeatherMap data to predict weather conditions using a KNN
classifier. Applies threshold-based logic to warn of climate-related
disasters (Flood, Drought, Cyclone).

Outputs:
  - LCD display (16x2)
  - Audible buzzer alert
  - ThingSpeak cloud upload
  - Android app notifications (via ThingSpeak)

Hardware:
  - Raspberry Pi 3
  - DHT11 (temperature + humidity)
  - LDR + MCP3208 ADC (light intensity)
  - 16x2 LCD (parallel interface)
  - Passive buzzer

Author: Ashvin Jaison Olickal (23BCE8207) and team
Project: Engineering Clinics, 3rd Sem, VIT-AP University (2024-25)
Guide: Prof. Virendra Kumar Verma
"""

import os
import sys
import time
import urllib.request

import numpy as np
import pandas as pd
import requests
import RPi.GPIO as GPIO
import Adafruit_DHT
from gpiozero import MCP3208
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier


# =========================================================================
# CONFIGURATION
# =========================================================================

# NOTE: In production, move these to a .env file — do NOT commit real keys.
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
THINGSPEAK_API_KEY = os.getenv("THINGSPEAK_API_KEY", "YOUR_THINGSPEAK_KEY")
CITY = "vijayawada"

OPENWEATHER_URL = (
    f"http://api.openweathermap.org/data/2.5/weather"
    f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric"
)

# Disaster thresholds
FLOOD_HUMIDITY_THRESHOLD = 90
DROUGHT_HUMIDITY_THRESHOLD = 30
CYCLONE_WIND_THRESHOLD = 60  # km/h

# GPIO pin assignments (BCM mode)
DHT_PIN = 4
BUZZER_PIN = 26
LCD_RS = 19
LCD_E = 13
LCD_D4 = 6
LCD_D5 = 5
LCD_D6 = 3
LCD_D7 = 2

# LCD constants
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
E_PULSE = 0.0005
E_DELAY = 0.0005


# =========================================================================
# HARDWARE SETUP
# =========================================================================

def setup_gpio():
    """Configure all GPIO pins used by the system."""
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    for pin in (LCD_E, LCD_RS, LCD_D4, LCD_D5, LCD_D6, LCD_D7):
        GPIO.setup(pin, GPIO.OUT)


# =========================================================================
# LCD DRIVER
# =========================================================================

def lcd_toggle_enable():
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    """Send one byte to the LCD in 4-bit mode."""
    GPIO.output(LCD_RS, mode)

    # High nibble
    GPIO.output(LCD_D4, bits & 0x10 == 0x10)
    GPIO.output(LCD_D5, bits & 0x20 == 0x20)
    GPIO.output(LCD_D6, bits & 0x40 == 0x40)
    GPIO.output(LCD_D7, bits & 0x80 == 0x80)
    lcd_toggle_enable()

    # Low nibble
    GPIO.output(LCD_D4, bits & 0x01 == 0x01)
    GPIO.output(LCD_D5, bits & 0x02 == 0x02)
    GPIO.output(LCD_D6, bits & 0x04 == 0x04)
    GPIO.output(LCD_D7, bits & 0x08 == 0x08)
    lcd_toggle_enable()


def lcd_init():
    """Initialize the LCD display."""
    lcd_byte(0x33, LCD_CMD)  # 8-bit init
    lcd_byte(0x32, LCD_CMD)  # 4-bit mode
    lcd_byte(0x06, LCD_CMD)  # Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # Display on, cursor off
    lcd_byte(0x28, LCD_CMD)  # 2 line display
    lcd_byte(0x01, LCD_CMD)  # Clear display
    time.sleep(E_DELAY)


def lcd_string(message, line):
    """Print a string on the given LCD line, padded to 16 chars."""
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


# =========================================================================
# MACHINE LEARNING
# =========================================================================

def train_classifier(data_path="Data1.csv"):
    """Train the KNN classifier on the historical weather dataset."""
    data = pd.read_csv(data_path)
    y = data["Result"]
    X = data.drop(["Result"], axis=1)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0
    )
    model = KNeighborsClassifier(n_neighbors=4)
    model.fit(X_train, y_train)
    return model


def interpret_prediction(y_pred):
    """Map the KNN class label to a human-readable weather state."""
    labels = {
        1: "Clear_Sky-high_Temperature",
        2: "Clear_Sky-Normal",
        3: "Rain-Low_temperatures",
    }
    return labels.get(int(y_pred), "Unknown")


def classify_disaster(humidity, temperature, wind_speed):
    """Rule-based disaster classifier applied on top of the ML output."""
    if humidity > FLOOD_HUMIDITY_THRESHOLD and temperature < 25:
        return "Flood Risk"
    if humidity < DROUGHT_HUMIDITY_THRESHOLD:
        return "Drought Risk"
    if wind_speed > CYCLONE_WIND_THRESHOLD:
        return "Cyclone Risk"
    return "Normal"


# =========================================================================
# EXTERNAL API
# =========================================================================

def fetch_openweather():
    """Pull current weather from OpenWeatherMap for the configured city."""
    response = requests.get(OPENWEATHER_URL, timeout=5)
    data = response.json()
    return {
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "description": data["weather"][0]["description"].replace(" ", "_"),
    }


def upload_to_thingspeak(temperature, humidity, ldr, api_temp, api_humidity,
                         wind, description, prediction):
    """Push all collected data fields to ThingSpeak channel."""
    url = (
        f"https://api.thingspeak.com/update?api_key={THINGSPEAK_API_KEY}"
        f"&field1={temperature}&field2={humidity}&field3={ldr}"
        f"&field4={api_temp}&field5={api_humidity}&field6={wind}"
        f"&field7={description}&field8={prediction}"
    )
    urllib.request.urlopen(url)


# =========================================================================
# MAIN LOOP
# =========================================================================

def main():
    setup_gpio()
    lcd_init()
    lcd_string("   WELCOME", LCD_LINE_1)

    ldr = MCP3208(channel=2)
    sensor = Adafruit_DHT.DHT11
    knn_model = train_classifier("Data1.csv")

    while True:
        # Local sensor readings
        humidity, temperature = Adafruit_DHT.read_retry(sensor, DHT_PIN)
        ldr_value = ldr.value / 1000
        print(f"TEMP: {temperature}  HUMD: {humidity}  LDR: {ldr_value}")

        # External weather API
        api_data = fetch_openweather()

        # ML prediction
        feature_vector = np.array(
            [[temperature, humidity, ldr_value, api_data["wind_speed"]]],
            dtype=np.float32,
        )
        y_pred = knn_model.predict(feature_vector)
        weather_state = interpret_prediction(y_pred[0])

        # Buzzer alert for rain conditions
        if y_pred[0] == 3:
            GPIO.output(BUZZER_PIN, 1)
            time.sleep(1)
            GPIO.output(BUZZER_PIN, 0)

        # Disaster classification
        disaster = classify_disaster(
            humidity, api_data["temp"], api_data["wind_speed"]
        )

        # Update LCD
        lcd_byte(0x01, LCD_CMD)  # Clear
        lcd_string(weather_state, LCD_LINE_1)
        lcd_string(disaster, LCD_LINE_2)

        # Push to cloud
        upload_to_thingspeak(
            temperature, humidity, ldr_value,
            api_data["temp"], api_data["humidity"], api_data["wind_speed"],
            api_data["description"], weather_state,
        )

        print(f"Predicted: {weather_state}  |  Disaster: {disaster}")
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down cleanly.")
    finally:
        GPIO.cleanup()
