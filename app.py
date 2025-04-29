from flask import Flask, render_template, jsonify, request
import sqlite3
import threading
import time
import requests
from datetime import datetime
import atexit
from sklearn.tree import DecisionTreeClassifier
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
import os

# =============================================
# KONFIGURASI APLIKASI
# =============================================
app = Flask(__name__)
print(f"Current working directory: {os.getcwd()}")
print(f"Absolute path to app: {os.path.abspath(__file__)}")

# Konfigurasi WiFi untuk NodeMCU
NODEMCU_CONFIG = {
    'base_url': 'http://192.168.8.137',  # URL NodeMCU
    'timeout': 5  # Timeout dalam detik
}

DATABASE = 'sensor_data.db'

# Auto mode settings
AUTO_SETTINGS = {
    'enabled': False,
    'lightThreshold': 500,
    'rainThreshold': 500
}

# Model info
MODEL_INFO = {
    'trained': False,
    'lastTraining': None,
    'accuracy': None
}

# =============================================
# FUNGSI KOMUNIKASI DENGAN NODEMCU
# =============================================
def get_nodemcu_data():
    """Dapatkan data sensor dari NodeMCU melalui API"""
    try:
        response = requests.get(f"{NODEMCU_CONFIG['base_url']}/api/data", timeout=NODEMCU_CONFIG['timeout'])
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting data from NodeMCU: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Connection error with NodeMCU: {e}")
        return None

def send_command_to_nodemcu(action):
    """Kirim perintah ke NodeMCU"""
    try:
        response = requests.post(
            f"{NODEMCU_CONFIG['base_url']}/api/control", 
            params={'action': action},
            timeout=NODEMCU_CONFIG['timeout']
        )
        if response.status_code == 200:
            result = response.json()
            print(f"Command sent successfully: {result}")
            return result
        else:
            print(f"Error sending command to NodeMCU: HTTP {response.status_code}")
            return {"success": False, "message": f"HTTP error {response.status_code}"}
    except requests.exceptions.RequestException as e:
        print(f"Connection error with NodeMCU: {e}")
        return {"success": False, "message": str(e)}

# =============================================
# INISIALISASI DATABASE
# =============================================
def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            ldr INTEGER,
            rain INTEGER,
            status TEXT,
            rotation INTEGER
        )
    ''')
    
    # Create settings table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# =============================================
# FUNCTIONS TO SAVE AND LOAD SETTINGS
# =============================================
def save_setting(key, value):
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
    ''', (key, str(value)))
    conn.commit()
    conn.close()

def load_setting(key, default=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

# Load saved settings on startup
def load_all_settings():
    global AUTO_SETTINGS, NODEMCU_CONFIG, MODEL_INFO
    
    # Load NodeMCU config
    base_url = load_setting('nodemcu_base_url', NODEMCU_CONFIG['base_url'])
    timeout = float(load_setting('nodemcu_timeout', NODEMCU_CONFIG['timeout']))
    
    NODEMCU_CONFIG['base_url'] = base_url
    NODEMCU_CONFIG['timeout'] = timeout
    
    # Load auto settings
    AUTO_SETTINGS['enabled'] = load_setting('auto_enabled', 'False') == 'True'
    AUTO_SETTINGS['lightThreshold'] = int(load_setting('light_threshold', AUTO_SETTINGS['lightThreshold']))
    AUTO_SETTINGS['rainThreshold'] = int(load_setting('rain_threshold', AUTO_SETTINGS['rainThreshold']))
    
    # Load model info
    MODEL_INFO['trained'] = load_setting('model_trained', 'False') == 'True'
    MODEL_INFO['lastTraining'] = load_setting('model_last_training')
    accuracy = load_setting('model_accuracy')
    MODEL_INFO['accuracy'] = float(accuracy) if accuracy else None

# Call this on startup
load_all_settings()

# =============================================
# MODEL AI WEATHER PREDICTOR (Decision Tree)
# =============================================
class WeatherPredictor:
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.window_size = 3  # Turunkan dari 6 menjadi 3
        self.threshold = 0.65
        
        # Try to load model if it exists
        try:
            self.load_model()  # Memanggil load_model() untuk memuat model jika ada
            MODEL_INFO['trained'] = True
        except (FileNotFoundError, EOFError):
            MODEL_INFO['trained'] = False

    def load_model(self, filename='weather_model.joblib'):
        print(f"Loading model from {os.path.abspath(filename)}")
        self.model = joblib.load(filename)
        self.scaler = joblib.load('scaler.save')
        print("Model loaded successfully")

    def create_dataset(self, scaled_data, y):  # Parameter sudah diperbaiki
        try:
            if len(scaled_data) <= self.window_size:
                raise ValueError(f"Data length ({len(scaled_data)}) must be greater than window size ({self.window_size})")
                
            X, y_processed = [], []
            for i in range(len(scaled_data) - self.window_size):
                # Flatten window menjadi 1D array
                window = scaled_data[i:(i+self.window_size-1), :].flatten()
                target = y[i+self.window_size-1]  # Ambil target dari y yang sudah dikonversi
                X.append(window)
                y_processed.append(target)
                
            if not X or not y_processed:
                raise ValueError("Failed to create dataset - empty X or y")
                
            return np.array(X), np.array(y_processed)
        except Exception as e:
            print(f"Error in create_dataset: {e}")
            raise

    def load_training_data(self):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute('SELECT ldr, rain FROM sensor_data ORDER BY timestamp')
        data = cursor.fetchall()
        conn.close()
        
        print(f"Found {len(data)} records for training")
        
        if len(data) < self.window_size + 10:
            raise ValueError(f"Insufficient data for training. Need at least {self.window_size + 10} records, but only have {len(data)}")
        
        # Konversi data string ke integer
        converted_data = []
        for row in data:
            try:
                ldr = int(row[0])
                rain = int(row[1])
                converted_data.append([ldr, rain])
            except (ValueError, TypeError) as e:
                print(f"Error converting data: {e}, row: {row}")
                continue
        
        if not converted_data:
            raise ValueError("No valid data after conversion")
                
        return np.array(converted_data)

    def preprocess_data(self, data):
        try:
            # Pisahkan fitur (ldr, rain) dan target (rain)
            X = data[:, :]  # Semua kolom sebagai fitur
            y = data[:, 1]  # Kolom rain sebagai target
            
            # Scaling hanya pada fitur
            scaled_X = self.scaler.fit_transform(X)
            
            # Konversi target ke kategori
            y = np.where(y < self.threshold, 1, 0).astype(int)
            
            # Create dataset dengan parameter yang benar
            X_processed, y_processed = self.create_dataset(scaled_X, y)
            
            return X_processed, y_processed
        except Exception as e:
            print(f"Error in preprocess_data: {e}")
            raise

    def build_model(self):
        self.model = DecisionTreeClassifier()

    # Metode train yang sudah diperbaiki dengan indentasi yang benar (dalam kelas)
    def train(self, epochs=20, batch_size=32):
        try:
            # Periksa jumlah data
            conn = sqlite3.connect(DATABASE)
            cursor = conn.execute('SELECT COUNT(*) FROM sensor_data')
            data_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"Data count: {data_count}")
            
            if data_count < self.window_size + 10:
                raise ValueError(f"Not enough data. Need at least {self.window_size + 10} records, but only have {data_count}")
            
            # Ambil data
            data = self.load_training_data()
            print(f"Data shape: {data.shape}")
            
            # Preprocessing
            try:
                X, y = self.preprocess_data(data)  # Sekarang mengembalikan X dan y yang sudah dipisah
                print(f"X shape: {X.shape}, y shape: {y.shape}")
                print(f"Sample y values: {np.unique(y, return_counts=True)}")  # Debug kelas
            except Exception as e:
                print(f"Error in preprocessing: {e}")
                raise
            
            # Jika data terlalu sedikit untuk dibagi
            if len(X) < 2:
                raise ValueError("Not enough data for training/testing split")
                
            split = max(1, int(0.8 * len(X)))
            
            # Build dan train model
            self.build_model()
            self.model.fit(X[:split], y[:split])
            
            # Simpan model setelah training
            self.save_model()
            
            # Hitung akurasi
            if len(X) > split:  # Pastikan ada data test
                accuracy = self.model.score(X[split:], y[split:])
            else:
                accuracy = self.model.score(X[:split], y[:split])  # Gunakan data training jika terpaksa
            
            # Update model info
            MODEL_INFO['trained'] = True
            MODEL_INFO['lastTraining'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            MODEL_INFO['accuracy'] = accuracy
            
            # Save model info to database
            save_setting('model_trained', 'True')
            save_setting('model_last_training', MODEL_INFO['lastTraining'])
            save_setting('model_accuracy', str(accuracy))
            
            return {"accuracy": accuracy}
        except Exception as e:
            print(f"Error during training: {e}")
            raise

    def predict_next_hour(self, recent_data):
        if not self.model:
            try:
                self.load_model()
            except (FileNotFoundError, EOFError):
                raise ValueError("Model not trained")
                
        scaled = self.scaler.transform(np.array(recent_data))
        scaled_window = scaled[-self.window_size+1:].flatten()  # Flatten menjadi 1D
        
        # Pastikan input shape sesuai dengan data training
        if scaled_window.shape[0] != (self.window_size-1)*2:
            raise ValueError("Invalid input shape for prediction")
        
        # Dapatkan prediksi dan probabilitas
        prediction = self.model.predict([scaled_window])[0]
        probability = self.model.predict_proba([scaled_window])[0][1]  # Probabilitas kelas 1 (hujan)
        
        return prediction, probability

    def save_model(self, filename='weather_model.joblib'):
        try:
            if not os.path.exists(os.path.dirname(filename)) and os.path.dirname(filename):
                os.makedirs(os.path.dirname(filename))
            print(f"Saving model to {os.path.abspath(filename)}")
            joblib.dump(self.model, filename)
            joblib.dump(self.scaler, 'scaler.save')
            print("Model saved successfully")
        except Exception as e:
            print(f"Error saving model: {e}")
            raise

# =============================================
# THREAD UNTUK MEMBACA DATA DARI NODEMCU
# =============================================
def nodemcu_reader():
    while True:
        try:
            # Ambil data dari NodeMCU
            data = get_nodemcu_data()
            
            # Jika berhasil dapatkan data
            if data:
                print(f"Data from NodeMCU: {data}")
                
                # Simpan data ke database
                conn = sqlite3.connect(DATABASE)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute(
                    'INSERT INTO sensor_data (timestamp, ldr, rain, status, rotation) VALUES (?, ?, ?, ?, ?)',
                    (timestamp, 
                     int(data.get('ldr', 0)),
                     int(data.get('rain', 0)),
                     data.get('status', ''),
                     int(data.get('rotation', 0)))
                )
                conn.commit()
                conn.close()
                
                # Check auto mode and send commands if needed
                if AUTO_SETTINGS['enabled']:
                    check_auto_conditions()
        except Exception as e:
            print(f"NodeMCU reader error: {str(e)}")
        
        time.sleep(3)  # Poll every 3 seconds

# Function to check auto mode conditions and send commands
def check_auto_conditions():
    try:
        # Get latest sensor data
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute('SELECT ldr, rain, status FROM sensor_data ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return
            
        ldr, rain, status = row
        
        # Check conditions and send commands
        if rain > AUTO_SETTINGS['rainThreshold'] and status != "TERTUTUP":
            # Rain detected, close the clothes line
            send_command_to_nodemcu('close')
            print("Auto mode: Rain detected - sending close command")
        elif ldr < AUTO_SETTINGS['lightThreshold'] and status != "TERTUTUP":
            # Low light (evening/night), close the clothes line
            send_command_to_nodemcu('close')
            print("Auto mode: Low light detected - sending close command")
        elif ldr > AUTO_SETTINGS['lightThreshold'] and rain < AUTO_SETTINGS['rainThreshold'] and status != "TERBUKA":
            # Good conditions (sunny, no rain), open the clothes line
            send_command_to_nodemcu('open')
            print("Auto mode: Good conditions - sending open command")
    except Exception as e:
        print(f"Error in auto mode: {e}")

# =============================================
# FUNGSI AUTO TRAINING MODEL
# =============================================
def auto_train_model():
    global weather_predictor
    while True:
        try:
            print("Automatic training started")
            # Check if we have enough data
            conn = sqlite3.connect(DATABASE)
            cursor = conn.execute('SELECT COUNT(*) FROM sensor_data')
            count = cursor.fetchone()[0]
            conn.close()
            
            if count >= (weather_predictor.window_size + 10):
                # Train model
                result = weather_predictor.train()
                print(f"Auto-training complete. Accuracy: {result['accuracy']}")
            else:
                print(f"Not enough data for training. Need {weather_predictor.window_size + 10}, have {count}")
        except Exception as e:
            print(f"Error in auto training: {e}")
        
        # Wait for 30 minutes before next training
        time.sleep(1800)

# Start NodeMCU reader thread
thread = threading.Thread(target=nodemcu_reader)
thread.daemon = True
thread.start()

# Start auto-training thread
auto_train_thread = threading.Thread(target=auto_train_model)
auto_train_thread.daemon = True
auto_train_thread.start()

# =============================================
# INITIALIZE WEATHER PREDICTOR
# =============================================
weather_predictor = WeatherPredictor()

# =============================================
# ROUTE FLASK
# =============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/realtime-monitoring')
def realtime_monitoring():
    return render_template('realtime.html')

@app.route('/control')
def control():
    return render_template('control.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/get_data')
def get_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute('SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"Data from database: {row}")  # Log untuk memeriksa data yang dikembalikan
        return jsonify({
            'timestamp': row[1],
            'ldr': row[2],
            'rain': row[3],
            'status': row[4],
            'rotation': row[5]
        })
    return jsonify({})  # Return empty JSON if no data found

# Add this debugging route to check data count
@app.route('/check-data-count')
def check_data_count():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute('SELECT COUNT(*) FROM sensor_data')
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'count': count})

@app.route('/send_command', methods=['POST'])
def send_command():
    try:
        command = request.json.get('command')
        if command == "open":
            result = send_command_to_nodemcu('open')
        elif command == "close":
            result = send_command_to_nodemcu('close')
        else:
            return jsonify({'status': 'error', 'message': 'Invalid command'}), 400
            
        return jsonify({'status': 'success', 'message': result.get('message', 'Command sent')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/train-model', methods=['POST'])
def handle_train():
    try:
        # First check if we have enough data
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute('SELECT COUNT(*) FROM sensor_data')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"Training model with {count} data records")
        
        if count < (weather_predictor.window_size + 10):
            return jsonify({'error': f'Data tidak cukup. Dibutuhkan minimal {weather_predictor.window_size + 10} data, saat ini hanya ada {count}'}), 400
            
        # Continue with training
        result = weather_predictor.train()
        
        return jsonify({
            'accuracy': result['accuracy']
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in train_model: {str(e)}\n{error_details}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict-weather')
def predict_weather():
    try:
        # Ambil 3 data terakhir dari database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute('SELECT ldr, rain FROM sensor_data ORDER BY timestamp DESC LIMIT 3')
        recent_data = cursor.fetchall()
        conn.close()
        
        # Lakukan prediksi
        global weather_predictor
        prediction, probability = weather_predictor.predict_next_hour(recent_data)
        
        # Konversi ke boolean dengan threshold
        will_rain = prediction >= weather_predictor.threshold
        return jsonify({
            'will_rain': will_rain,
            'probability': probability
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================
# ROUTES FOR SETTINGS PAGE
# =============================================

@app.route('/get-config')
def get_config():
    """Get current system configuration"""
    return jsonify({
        'base_url': NODEMCU_CONFIG['base_url'],
        'timeout': NODEMCU_CONFIG['timeout']
    })

@app.route('/save-config', methods=['POST'])
def save_config():
    try:
        # Get configuration from request
        config = request.json
        print(f"Saving config: {config}")
        
        # Update NodeMCU configuration
        NODEMCU_CONFIG['base_url'] = config['base_url']
        NODEMCU_CONFIG['timeout'] = float(config['timeout'])
        
        # Save settings to database
        save_setting('nodemcu_base_url', config['base_url'])
        save_setting('nodemcu_timeout', str(config['timeout']))
        
        return jsonify({'status': 'success', 'message': 'Configuration saved!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-auto-settings')
def get_auto_settings():
    """Get auto mode settings"""
    return jsonify(AUTO_SETTINGS)

@app.route('/save-auto-settings', methods=['POST'])
def save_auto_settings():
    try:
        # Get settings from request
        settings = request.json
        print(f"Saving auto settings: {settings}")
        
        # Update auto settings
        AUTO_SETTINGS['enabled'] = settings['enabled']
        AUTO_SETTINGS['lightThreshold'] = int(settings['lightThreshold'])
        AUTO_SETTINGS['rainThreshold'] = int(settings['rainThreshold'])
        
        # Save settings to database
        save_setting('auto_enabled', str(settings['enabled']))
        save_setting('light_threshold', str(settings['lightThreshold']))
        save_setting('rain_threshold', str(settings['rainThreshold']))
        
        return jsonify({'status': 'success', 'message': 'Auto settings saved!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-model-info')
def get_model_info():
    """Get model information"""
    return jsonify(MODEL_INFO)

@app.route('/check-nodemcu')
def check_nodemcu():
    """Check if NodeMCU is available"""
    try:
        response = requests.get(f"{NODEMCU_CONFIG['base_url']}/api/status", timeout=NODEMCU_CONFIG['timeout'])
        if response.status_code == 200:
            return jsonify({'status': 'connected', 'message': 'NodeMCU is connected'})
        else:
            return jsonify({'status': 'error', 'message': f'NodeMCU returned HTTP {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Cannot connect to NodeMCU: {str(e)}'}), 500

@app.route('/view-data')
def view_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensor_data")
    rows = cursor.fetchall()
    conn.close()

    # Menampilkan data dalam bentuk JSON
    return jsonify(rows)

# =============================================
# MAIN EXECUTION
# =============================================
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )