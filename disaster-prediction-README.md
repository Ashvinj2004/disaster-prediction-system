# 🌦️ Raspberry Pi Weather Station with Disaster Prediction

**An IoT-based climate monitoring system that fuses local sensor data with global weather APIs and predicts climate-related disasters using machine learning — designed for affordability and rural deployment.**

*Engineering Clinics Project · VIT-AP University · 3rd Semester (2024–25)*
*Guided by Prof. Virendra Kumar Verma · Team of 6 · Grade: S*

---

## 🎯 What This Project Does

Traditional weather stations are expensive, sparsely deployed, and rarely provide **disaster warnings** to the communities that need them most. This project addresses that gap.

Built on a **Raspberry Pi 3**, the system:

1. **Reads local environmental data** in real time from sensors (temperature, humidity, light intensity)
2. **Fetches external weather data** from the OpenWeatherMap API (wind speed, atmospheric pressure, conditions)
3. **Runs a KNN classifier** trained to categorize current weather conditions
4. **Applies threshold-based logic** to flag disaster risks (Flood, Drought, Cyclone)
5. **Displays results locally** on a 16×2 LCD with an audible buzzer alert
6. **Streams data to ThingSpeak cloud** for long-term monitoring and visualization
7. **Pushes alerts to a companion Android app** built with MIT App Inventor

Total hardware cost: **under ₹4,500** — vs. tens of thousands for commercial-grade stations.

---

## 🛠️ Tech Stack

**Hardware**
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi_3-A22846?style=flat-square&logo=raspberrypi&logoColor=white)
DHT11 · LDR (via MCP3208 ADC) · 16×2 LCD · Buzzer

**Software**
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)

**Cloud & Mobile**
![ThingSpeak](https://img.shields.io/badge/ThingSpeak-D22128?style=flat-square)
![MIT App Inventor](https://img.shields.io/badge/MIT_App_Inventor-A5CF4C?style=flat-square)
![Android](https://img.shields.io/badge/Android-3DDC84?style=flat-square&logo=android&logoColor=white)

**APIs & Libraries**
OpenWeatherMap API · `Adafruit_DHT` · `RPi.GPIO` · `gpiozero`

---

## 🧠 System Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐
│  DHT11 (Temp,   │      │                  │      │ OpenWeatherMap │
│  Humidity)      ├─────►│                  │◄─────┤     API        │
├─────────────────┤      │                  │      └────────────────┘
│  LDR (Light)    ├─────►│  Raspberry Pi 3  │
├─────────────────┤      │                  │      ┌────────────────┐
│ MCP3208 ADC     │      │  • KNN Model     ├─────►│  ThingSpeak    │
└─────────────────┘      │  • Threshold     │      │  (Cloud)       │
                         │    logic         │      └───────┬────────┘
                         │  • REST client   │              │
                         └────────┬─────────┘              ▼
                                  │              ┌────────────────┐
                    ┌─────────────┴────────┐     │  Android App   │
                    ▼                      ▼     │  (MIT App Inv.)│
             ┌───────────┐         ┌──────────┐  └────────────────┘
             │ 16×2 LCD  │         │  Buzzer  │
             └───────────┘         └──────────┘
```

---

## 🔬 Machine Learning Approach

**Model:** K-Nearest Neighbors classifier (`k=4`)
**Features:** temperature, humidity, LDR value, wind speed
**Target classes:** Clear Sky (High Temp), Clear Sky (Normal), Rain (Low Temp)
**Split:** 80/20 train/test

**Disaster prediction layer (rule-based, applied on top of ML output):**

| Condition | Prediction |
|---|---|
| Humidity > 90% AND Temp < 25°C | 🌊 Flood Risk |
| Humidity < 30% | 🏜️ Drought Risk |
| Wind speed > 60 km/h | 🌀 Cyclone Risk |
| Otherwise | ✅ Normal |

Performance was evaluated using a confusion matrix across the classification categories (see project report).

> **Design note:** We deliberately combined a lightweight ML classifier with interpretable threshold logic. This kept the system explainable and reliable given our dataset size — a pragmatic choice for edge devices where model debugging in the field must be straightforward.

---

## 📁 Repository Structure

```
disaster-prediction-system/
│
├── src/
│   ├── weather_station.py          # Main Raspberry Pi program (sensor + ML + LCD + cloud)
│   └── (helper scripts)
│
├── android_app/
│   └── weather_report.apk          # Compiled Android app (MIT App Inventor)
│
├── docs/
│   ├── project_report.pdf          # Full academic report
│   └── circuit_diagram.png         # Wiring reference
│
├── data/
│   └── README.md                   # Note: original dataset lost on Pi; sample structure provided
│
├── .gitignore
└── README.md
```

---

## ⚙️ How It Works (Runtime)

1. Raspberry Pi boots and initializes GPIO pins, LCD, and sensors
2. Displays "WELCOME" on LCD
3. Loads training data (`Data1.csv`) and trains KNN classifier in-memory
4. Enters infinite loop:
   - Reads temp + humidity from DHT11
   - Reads light from LDR through MCP3208 ADC
   - Fetches remote weather from OpenWeatherMap API
   - Runs KNN prediction on combined feature vector
   - Applies disaster threshold logic
   - Updates LCD with predicted state + disaster warning
   - Triggers buzzer if rain conditions detected
   - Pushes all fields to ThingSpeak via REST
   - Sleeps 2 seconds, repeats

---

## 📱 Android App

A companion Android app (`weather_report.apk`) built in **MIT App Inventor** provides:
- Real-time weather data pulled from ThingSpeak
- Disaster alert notifications
- Historical trend viewing

*APK is included in `/android_app/` — sideload on any Android device to test.*

---

## 💡 Why This Project Matters

**The problem:** Rural and underserved communities in disaster-prone regions of India lack access to real-time weather monitoring. Government stations are sparse; commercial IoT weather solutions cost lakhs of rupees.

**Our contribution:** A **₹4,500 open-source alternative** that combines local sensing, cloud storage, ML-based prediction, and mobile alerts — deployable by anyone with basic electronics knowledge.

**Real applications:**
- 🌾 **Agriculture** — irrigation planning, crop protection
- 🚨 **Disaster preparedness** — early flood/cyclone alerts for at-risk villages
- 📊 **Climate research** — long-term microclimate data collection
- 🏫 **Educational** — hands-on IoT + ML teaching tool

---

## 🚧 Known Limitations & Future Work

**Honest limitations of the current system:**
- Training dataset (`Data1.csv`) was relatively small and lost after the project concluded — model would benefit from retraining on a larger, region-specific corpus
- Threshold values are hand-tuned rather than learned
- KNN classifier is a strong baseline but can be upgraded (Random Forest, gradient-boosted models were listed as candidates in the report)
- No seismic sensor — earthquake threshold logic exists in code but is unused

**Planned enhancements:**
- [ ] Retrain with larger multi-region weather dataset
- [ ] Replace threshold logic with a second-stage learned classifier
- [ ] Add automated response actuators (e.g., motorized rain covers)
- [ ] Expand sensor suite (barometric pressure, rainfall, seismic)
- [ ] Deploy multi-node mesh network for wider area coverage


## 📚 References

1. *Modular Weather and Environment Monitoring Systems using Raspberry Pi*, IJERT Vol. 3 Issue 9, 2014
2. *Low-Cost Controller-Based Weather Monitoring System*, CMA Journal, 2006
3. [DHT11 Sensor Datasheet — Components101](https://components101.com/sensors/dht11-temperature-sensor)
4. [ThingSpeak IoT Platform](https://thingspeak.com/)

---

## 👤 Author

**Ashvin Jaison Olickal**
B.Tech Computer Science · VIT-AP University · Class of 2027
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://linkedin.com/in/YOUR-HANDLE)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/Ashvinj2004)

---

