# -*- coding: utf-8 -*-
"""
Скрипт для работы с датчиком RF603HS
- Чтение данных с датчика через последовательный порт
- Сохранение в CSV (расстояние_мм, номер_точки, время_сек)
- Динамическая визуализация
- Автоматический анализ затухающих колебаний
"""

import serial
import serial.tools.list_ports
import struct
import time
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import find_peaks, savgol_filter, argrelextrema
from datetime import datetime
import threading
from collections import deque

class RF603Sensor:
    """Класс для работы с датчиком RF603HS"""

    def __init__(self):
        self.serial_port = None
        self.is_connected = False
        self.device_info = {}
        self.data_buffer = deque(maxlen=10000)
        self.recording = False
        self.start_time = None

    @staticmethod
    def list_available_ports():
        """Список доступных COM-портов"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        print("\n" + "="*60)
        print("ДОСТУПНЫЕ COM-ПОРТЫ:")
        print("="*60)

        for i, port in enumerate(ports, 1):
            print(f"{i}. {port.device}")
            print(f"   Описание: {port.description}")
            print(f"   HWID: {port.hwid}")
            print("-"*60)
            available_ports.append(port.device)

        if not available_ports:
            print("Нет доступных портов!")

        return available_ports

    def connect(self, port, baudrate=9600, address=1):
        """Подключение к датчику"""
        try:
            print(f"\n🔌 Подключение к {port} на скорости {baudrate} бод...")

            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=2
            )

            time.sleep(0.5)  # Ждем стабилизации

            # Очищаем буфер
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

            # Идентификация устройства
            if self.identify_device(address):
                self.is_connected = True
                print("✅ Подключение успешно!")
                return True
            else:
                print("❌ Не удалось идентифицировать датчик")
                self.disconnect()
                return False

        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def identify_device(self, address=1):
        """Идентификация устройства (запрос 01h)"""
        try:
            # Формируем запрос идентификации
            inc0 = address & 0x7F  # Адрес (7 бит)
            inc1 = 0x80 | 0x01     # 1000 0001 (код запроса 01h)

            request = bytes([inc0, inc1])
            self.serial_port.write(request)

            time.sleep(0.1)

            # Читаем ответ (16 байт = 8 значений по 2 байта)
            response = self.serial_port.read(16)

            if len(response) >= 16:
                # Декодируем ответ
                device_type = self._decode_byte(response[0], response[1])
                firmware_version = self._decode_byte(response[2], response[3])
                serial_number = self._decode_word(response[4:8])
                base_distance = self._decode_word(response[8:12])
                measurement_range = self._decode_word(response[12:16])

                self.device_info = {
                    'type': device_type,
                    'firmware': firmware_version,
                    'serial': serial_number,
                    'base_distance': base_distance,
                    'range': measurement_range
                }

                print("\n" + "="*60)
                print("ИНФОРМАЦИЯ О ДАТЧИКЕ:")
                print("="*60)
                print(f"Тип устройства: {device_type}")
                print(f"Версия ПО: {firmware_version}")
                print(f"Серийный номер: {serial_number}")
                print(f"Базовое расстояние: {base_distance} мм")
                print(f"Диапазон измерения: {measurement_range} мм")
                print("="*60)

                return True

            return False

        except Exception as e:
            print(f"❌ Ошибка идентификации: {e}")
            return False

    def _decode_byte(self, byte0, byte1):
        """Декодирование байта из двух посылок"""
        # byte0: 1 0 CNT CNT DAT3 DAT2 DAT1 DAT0
        # byte1: 1 0 CNT CNT DAT7 DAT6 DAT5 DAT4
        low_nibble = byte0 & 0x0F
        high_nibble = byte1 & 0x0F
        return (high_nibble << 4) | low_nibble

    def _decode_word(self, bytes_data):
        """Декодирование слова (2 байта) из 4 посылок"""
        byte0 = self._decode_byte(bytes_data[0], bytes_data[1])
        byte1 = self._decode_byte(bytes_data[2], bytes_data[3])
        return (byte1 << 8) | byte0

    def request_single_measurement(self, address=1):
        """Запрос одного измерения (запрос 06h)"""
        try:
            inc0 = address & 0x7F
            inc1 = 0x80 | 0x06

            request = bytes([inc0, inc1])
            self.serial_port.write(request)

            time.sleep(0.05)

            response = self.serial_port.read(4)

            if len(response) >= 4:
                result = self._decode_word(response[0:4])
                # Преобразуем в мм
                distance_mm = (result * self.device_info['range']) / 0x4000
                return distance_mm

            return None

        except Exception as e:
            print(f"❌ Ошибка чтения: {e}")
            return None

    def start_data_stream(self, address=1):
        """Начать поток данных (запрос 07h)"""
        try:
            inc0 = address & 0x7F
            inc1 = 0x80 | 0x07

            request = bytes([inc0, inc1])
            self.serial_port.write(request)
            print("📡 Поток данных запущен")

        except Exception as e:
            print(f"❌ Ошибка запуска потока: {e}")

    def stop_data_stream(self, address=1):
        """Остановить поток данных (запрос 08h)"""
        try:
            inc0 = address & 0x7F
            inc1 = 0x80 | 0x08

            request = bytes([inc0, inc1])
            self.serial_port.write(request)
            print("⏹ Поток данных остановлен")

        except Exception as e:
            print(f"❌ Ошибка остановки потока: {e}")

    def read_stream_data(self):
        """Чтение данных из потока"""
        try:
            if self.serial_port.in_waiting >= 4:
                response = self.serial_port.read(4)
                if len(response) >= 4:
                    # Проверяем что это поток данных (старший бит = 1)
                    if (response[0] & 0x80) and (response[2] & 0x80):
                        result = self._decode_word(response[0:4])
                        # Преобразуем в мм
                        distance_mm = (result * self.device_info['range']) / 0x4000
                        return distance_mm
            return None

        except Exception as e:
            return None

    def change_baudrate(self, new_baudrate, address=1):
        """Изменить скорость передачи данных"""
        try:
            # Рассчитываем значение параметра (в дискретах по 2400)
            param_value = new_baudrate // 2400

            if param_value < 1 or param_value > 192:
                print(f"❌ Недопустимая скорость: {new_baudrate}")
                return False

            # Запрос записи параметра (03h)
            inc0 = address & 0x7F
            inc1 = 0x80 | 0x03

            # Сообщение: код параметра (04h) + значение
            msg = self._encode_byte(0x04) + self._encode_byte(param_value)

            request = bytes([inc0, inc1]) + bytes(msg)
            self.serial_port.write(request)

            time.sleep(0.1)

            # Сохраняем во Flash (04h)
            inc1_save = 0x80 | 0x04
            msg_save = self._encode_byte(0xAA) + self._encode_byte(0xAA)
            request_save = bytes([inc0, inc1_save]) + bytes(msg_save)
            self.serial_port.write(request_save)

            time.sleep(0.2)

            # Переподключаемся с новой скоростью
            port = self.serial_port.port
            self.disconnect()
            time.sleep(0.5)

            return self.connect(port, new_baudrate, address)

        except Exception as e:
            print(f"❌ Ошибка изменения скорости: {e}")
            return False

    def _encode_byte(self, value):
        """Кодирование байта в две посылки"""
        low_nibble = value & 0x0F
        high_nibble = (value >> 4) & 0x0F

        byte0 = 0x80 | low_nibble
        byte1 = 0x80 | high_nibble

        return [byte0, byte1]

    def disconnect(self):
        """Отключение от датчика"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("🔌 Отключено от датчика")
        self.is_connected = False


class DataRecorder:
    """Класс для записи данных"""

    def __init__(self, sensor):
        self.sensor = sensor
        self.data_points = []
        self.recording = False
        self.record_thread = None
        self.start_time = None
        self.point_counter = 0

    def start_recording(self, filename=None):
        """Начать запись данных"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rf603_data_{timestamp}.csv"

        self.filename = filename
        self.data_points = []
        self.recording = True
        self.start_time = time.time()
        self.point_counter = 0

        # Запускаем поток данных
        self.sensor.start_data_stream()

        # Запускаем поток записи
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.daemon = True
        self.record_thread.start()

        print(f"🔴 ЗАПИСЬ НАЧАТА → {filename}")

    def _record_loop(self):
        """Цикл записи данных"""
        while self.recording:
            distance = self.sensor.read_stream_data()

            if distance is not None:
                elapsed_time = time.time() - self.start_time

                data_point = {
                    'Расстояние_мм': distance,
                    'Номер_точки': self.point_counter,
                    'Временная_метка': elapsed_time
                }

                self.data_points.append(data_point)
                self.point_counter += 1

                # Выводим прогресс каждые 100 точек
                if self.point_counter % 100 == 0:
                    print(f"📊 Записано точек: {self.point_counter}, Время: {elapsed_time:.2f} сек")

            time.sleep(0.001)  # Небольшая задержка

    def stop_recording(self):
        """Остановить запись"""
        if not self.recording:
            return None

        self.recording = False
        self.sensor.stop_data_stream()

        if self.record_thread:
            self.record_thread.join(timeout=2)

        # Сохраняем в CSV
        if self.data_points:
            df = pd.DataFrame(self.data_points)
            df.to_csv(self.filename, sep=';', index=False, encoding='utf-8')

            print(f"\n✅ ЗАПИСЬ ЗАВЕРШЕНА:")
            print(f"   📁 Файл: {self.filename}")
            print(f"   📊 Точек: {len(self.data_points)}")
            print(f"   ⏱️ Время: {self.data_points[-1]['Временная_метка']:.2f} сек")

            return self.filename

        return None


class RF603OscillationAnalyzer:
    """Класс для анализа затухающих колебаний (из dekrement.py)"""

    def __init__(self):
        self.data = None
        self.processed_data = None
        self.original_processed_data = None
        self.oscillation_start = 0
        self.oscillation_end = 0
        self.corrected_peaks = None
        self.current_period = None
        self.current_frequency = None
        self.log_decrement = None
        self.loss_factor = None
        self.damping_ratio = None

    def load_csv(self, filename):
        """Загрузка CSV файла"""
        try:
            self.data = pd.read_csv(filename, delimiter=';', encoding='utf-8')
            print(f"✅ Данные загружены из: {filename}")
            print(f"📊 Загружено {len(self.data)} строк")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def normalize_data(self):
        """Нормировка данных"""
        if self.data is None:
            return False

        try:
            self.processed_data = self.data.copy()
            first_distance = self.processed_data.iloc[0]['Расстояние_мм']
            self.processed_data['Расстояние_норм'] = (
                self.processed_data['Расстояние_мм'] - first_distance
            )

            self.original_processed_data = self.processed_data.copy()
            print(f"✅ Нормировка выполнена. Первое значение: {first_distance:.3f} мм")
            return True
        except Exception as e:
            print(f"❌ Ошибка нормировки: {e}")
            return False

    def find_release_point(self, threshold=0.5):
        """Поиск начала колебаний"""
        if self.processed_data is None:
            return 0

        distances = self.processed_data['Расстояние_норм'].values

        for i in range(1, len(distances) - 10):
            window = distances[i:i+10]
            if np.max(window) - np.min(window) > threshold:
                release_point = max(0, i - 5)
                print(f"📍 Начало колебаний найдено в точке {release_point}")
                return release_point

        print("⚠️ Начало колебаний не найдено")
        return 0

    def auto_crop_oscillations(self, duration_after_start=1.0):
        """Автоматическая обрезка колебаний"""
        if self.processed_data is None:
            return False, None, None, None

        try:
            # Находим начало
            start_idx = self.find_release_point(threshold=0.5)
            if start_idx == 0:
                return False, None, None, None

            start_time = self.processed_data.iloc[start_idx]['Временная_метка']
            end_time = start_time + duration_after_start

            # Обрезаем
            start_mask = self.processed_data['Временная_метка'] >= start_time
            end_mask = self.processed_data['Временная_метка'] <= end_time

            if not any(start_mask) or not any(end_mask):
                return False, None, None, None

            start_idx = self.processed_data[start_mask].index[0]
            end_idx = self.processed_data[end_mask].index[-1]

            self.processed_data = self.processed_data.iloc[start_idx:end_idx + 1].reset_index(drop=True)
            self.oscillation_start = start_idx
            self.oscillation_end = end_idx

            print(f"✅ Данные обрезаны: {start_idx}-{end_idx}")

            # Рассчитываем параметры
            period, frequency, peaks = self.calculate_period_frequency_improved()

            return True, period, frequency, peaks

        except Exception as e:
            print(f"❌ Ошибка обрезки: {e}")
            return False, None, None, None

    def calculate_period_frequency_improved(self):
        """Расчет периода и частоты"""
        if self.processed_data is None:
            return None, None, None

        try:
            distances = self.processed_data['Расстояние_норм'].values
            timestamps = self.processed_data['Временная_метка'].values

            # Сглаживание
            if len(distances) > 11:
                distances_smooth = savgol_filter(distances, 11, 3)
            else:
                distances_smooth = distances

            # Поиск пиков
            amplitude = np.max(distances_smooth) - np.min(distances_smooth)
            peaks, _ = find_peaks(
                distances_smooth,
                height=amplitude * 0.1,
                distance=max(3, len(distances_smooth) // 20),
                prominence=amplitude * 0.05
            )

            if len(peaks) < 2:
                print("❌ Недостаточно пиков")
                return None, None, None

            print(f"📈 Найдено пиков: {len(peaks)}")

            # Рассчитываем периоды
            periods = []
            for i in range(len(peaks) - 1):
                period = timestamps[peaks[i + 1]] - timestamps[peaks[i]]
                periods.append(period)

            # Фильтрация выбросов
            if len(periods) >= 3:
                Q1 = np.percentile(periods, 25)
                Q3 = np.percentile(periods, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                filtered_periods = [p for p in periods if lower_bound <= p <= upper_bound]
            else:
                filtered_periods = periods

            if not filtered_periods:
                filtered_periods = periods

            avg_period = np.mean(filtered_periods)
            frequency = 1.0 / avg_period if avg_period > 0 else 0

            self.current_period = avg_period
            self.current_frequency = frequency

            print(f"⏱️ Период: {avg_period:.6f} сек")
            print(f"📊 Частота: {frequency:.2f} Гц")

            # Логарифмический декремент
            self.calculate_logarithmic_decrement(peaks)

            return avg_period, frequency, peaks

        except Exception as e:
            print(f"❌ Ошибка расчета: {e}")
            return None, None, None

    def calculate_logarithmic_decrement(self, peaks):
        """Расчет логарифмического декремента"""
        if peaks is None or len(peaks) < 2:
            return None, None, None

        try:
            distances = self.processed_data['Расстояние_норм'].values
            amplitudes = distances[peaks]

            decrements = []
            for i in range(len(peaks) - 1):
                A_i = abs(amplitudes[i])
                A_i_plus_1 = abs(amplitudes[i + 1])

                if A_i_plus_1 > 0:
                    delta = np.log(A_i / A_i_plus_1)
                    decrements.append(delta)

            if not decrements:
                return None, None, None

            avg_decrement = np.mean(decrements)
            damping_ratio = avg_decrement / np.sqrt(4 * np.pi**2 + avg_decrement**2)
            loss_factor = 2 * damping_ratio

            self.log_decrement = avg_decrement
            self.damping_ratio = damping_ratio
            self.loss_factor = loss_factor

            print(f"📉 Логарифмический декремент (δ): {avg_decrement:.6f}")
            print(f"📉 Коэффициент демпфирования (ζ): {damping_ratio:.6f}")
            print(f"📉 Коэффициент потерь (η): {loss_factor:.6f}")

            return avg_decrement, damping_ratio, loss_factor

        except Exception as e:
            print(f"❌ Ошибка расчета декремента: {e}")
            return None, None, None

    def plot_results(self):
        """Построение графиков результатов"""
        if self.processed_data is None:
            print("❌ Нет данных для графиков")
            return

        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

            time_data = self.processed_data['Временная_метка']
            distance_norm = self.processed_data['Расстояние_норм']

            # График 1: Затухающие колебания
            ax1.plot(time_data, distance_norm, 'b-', linewidth=1.5, label='Колебания')
            ax1.set_xlabel('Время (сек)', fontsize=12)
            ax1.set_ylabel('Нормированное расстояние (мм)', fontsize=12)
            ax1.set_title('Затухающие колебания', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            # Добавляем информацию
            if self.current_period and self.current_frequency:
                info_text = f'Период: {self.current_period:.6f} сек\nЧастота: {self.current_frequency:.2f} Гц'
                if self.log_decrement:
                    info_text += f'\nЛог. декремент (δ): {self.log_decrement:.6f}'
                    info_text += f'\nКоэф. потерь (η): {self.loss_factor:.6f}'

                ax1.text(0.02, 0.98, info_text,
                        transform=ax1.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                        fontsize=10)

            # График 2: Расстояние от времени
            ax2.plot(time_data, self.processed_data['Расстояние_мм'], 'g-',
                    linewidth=1.5, label='Расстояние')
            ax2.set_xlabel('Время (сек)', fontsize=12)
            ax2.set_ylabel('Расстояние (мм)', fontsize=12)
            ax2.set_title('Зависимость расстояния от времени', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend()

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"❌ Ошибка построения графиков: {e}")


def main():
    """Главная функция"""
    print("="*70)
    print(" "*15 + "RF603HS LOGGER & ANALYZER")
    print("="*70)

    sensor = RF603Sensor()

    # 1. Показываем доступные порты
    available_ports = sensor.list_available_ports()

    if not available_ports:
        print("❌ Нет доступных портов. Завершение.")
        return

    # 2. Выбираем порт
    try:
        port_choice = int(input(f"\nВыберите порт (1-{len(available_ports)}): ")) - 1
        selected_port = available_ports[port_choice]
    except (ValueError, IndexError):
        print("❌ Неверный выбор")
        return

    # 3. Выбираем скорость
    print("\nДоступные скорости (бод):")
    print("1. 9600 (по умолчанию)")
    print("2. 19200")
    print("3. 57600")
    print("4. 115200")
    print("5. 460800")

    baud_rates = {1: 9600, 2: 19200, 3: 57600, 4: 115200, 5: 460800}
    try:
        baud_choice = int(input("Выберите скорость (1-5): "))
        selected_baud = baud_rates.get(baud_choice, 9600)
    except ValueError:
        selected_baud = 9600

    # 4. Подключаемся
    if not sensor.connect(selected_port, selected_baud):
        print("❌ Не удалось подключиться")
        return

    # 5. Запись данных
    recorder = DataRecorder(sensor)

    print("\n" + "="*70)
    print("ЗАПИСЬ ДАННЫХ")
    print("="*70)
    print("Нажмите ENTER для начала записи...")
    input()

    recorder.start_recording()

    print("\nНажмите ENTER для остановки записи...")
    input()

    filename = recorder.stop_recording()

    if filename is None:
        print("❌ Нет данных для сохранения")
        sensor.disconnect()
        return

    # 6. Анализ данных
    print("\n" + "="*70)
    print("АВТОМАТИЧЕСКИЙ АНАЛИЗ ДАННЫХ")
    print("="*70)

    analyzer = RF603OscillationAnalyzer()

    if not analyzer.load_csv(filename):
        sensor.disconnect()
        return

    if not analyzer.normalize_data():
        sensor.disconnect()
        return

    # Автоматическая обрезка
    print("\nДлительность анализа после начала колебаний (сек) [по умолчанию: 1.0]:")
    try:
        duration = float(input("Введите длительность: ") or "1.0")
    except ValueError:
        duration = 1.0

    success, period, frequency, peaks = analyzer.auto_crop_oscillations(duration)

    if success:
        print("\n" + "="*70)
        print("РЕЗУЛЬТАТЫ АНАЛИЗА")
        print("="*70)
        print(f"⏱️ Период колебаний: {period:.6f} сек")
        print(f"📊 Частота: {frequency:.2f} Гц")

        if analyzer.log_decrement:
            print(f"📉 Логарифмический декремент: {analyzer.log_decrement:.6f}")
            print(f"📉 Коэффициент демпфирования: {analyzer.damping_ratio:.6f}")
            print(f"📉 Коэффициент потерь: {analyzer.loss_factor:.6f}")

        # Показываем графики
        print("\n📊 Отображение графиков...")
        analyzer.plot_results()
    else:
        print("❌ Не удалось провести автоматический анализ")

    sensor.disconnect()
    print("\n✅ Работа завершена!")


if __name__ == "__main__":
    main()
