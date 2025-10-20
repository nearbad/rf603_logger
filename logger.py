# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import csv
import datetime
import time
import struct
import os
import sys
import matplotlib.pyplot as plt
import numpy as np

class RF603UltraFastLogger:
    def __init__(self):
        self.ser = None
        self.measurement_count = 0
        self.sensor_range = 250
        self.base_distance = 80
        self.is_running = False
        self.data_dir = "rf603_data"  # Папка для данных
        self.MIN_DISTANCE = 100.0  # Дефолтное минимальное расстояние в мм
        self.MAX_DISTANCE = 160.0  # Дефолтное максимальное расстояние в мм
        self.TARGET_FREQUENCY = 2000  # Целевая частота в Гц
        self.TIMEOUT_DURATION = 1.5  # Таймаут 1.5 секунды без корректных данных
        self.selected_port = None
        self.selected_baudrate = None
        
    def connect(self, port='COM3', baudrate=921600):
        """Подключение к датчику РФ603"""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.001  # Уменьшили timeout для высокой частоты
            )
            time.sleep(1)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"✅ Подключено к {port} на скорости {baudrate}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def close(self):
        """Закрытие соединения"""
        self.is_running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Порт закрыт")

    def reconnect(self):
        """Переподключение к датчику"""
        self.close()
        time.sleep(0.5)  # Небольшая пауза перед переподключением
        if self.selected_port and self.selected_baudrate:
            return self.connect(self.selected_port, self.selected_baudrate)
        return False

    def create_experiment_directory(self, experiment_name):
        """Создание папки для эксперимента"""
        experiment_dir = os.path.join(self.data_dir, experiment_name)
        if not os.path.exists(experiment_dir):
            os.makedirs(experiment_dir)
            print(f"📁 Создана папка эксперимента: {experiment_dir}")
        return experiment_dir

    def parse_riftek_binary_response(self, data):
        """Парсинг бинарного ответа по протоколу RIFTEK"""
        if not data or len(data) < 2:
            return None
            
        try:
            if not all(byte & 0x80 for byte in data):
                return None
                
            result_bytes = []
            for i in range(0, len(data) - 1, 2):
                if i + 1 < len(data):
                    low_byte = data[i] & 0x0F
                    high_byte = data[i + 1] & 0x0F
                    combined_byte = (high_byte << 4) | low_byte
                    result_bytes.append(combined_byte)
            
            return result_bytes
        except Exception:
            return None

    def decode_measurement(self, data):
        """Декодирование измерения расстояния"""
        if not data or len(data) < 2:
            return None
            
        try:
            raw_value = struct.unpack('<H', bytes(data[:2]))[0]
            distance_mm = (raw_value * self.sensor_range) / 16384.0
            return distance_mm
        except Exception:
            return None

    def get_measurement_ultra_fast(self):
        """Ультра-быстрое получение измерения"""
        try:
            self.ser.write(b'R2\r\n')
            response = self.ser.read(4)  # Читаем ровно 4 байта
            
            if response and len(response) == 4:
                parsed = self.parse_riftek_binary_response(response)
                if parsed:
                    distance = self.decode_measurement(parsed)
                    # Проверяем ограничение по расстоянию
                    if distance is not None and self.MIN_DISTANCE <= distance <= self.MAX_DISTANCE:
                        return distance
                    else:
                        # Возвращаем None для значений вне допустимого диапазона
                        return None
            return None
        except Exception:
            return None

    def identify_device(self):
        """Идентификация устройства"""
        print("🔍 Идентификация устройства...")
        
        try:
            self.ser.write(b'V\r\n')
            time.sleep(0.2)
            
            response = self.ser.read(16)  # Ожидаем 16 байт для идентификации
            if response:
                parsed = self.parse_riftek_binary_response(response)
                if parsed and len(parsed) >= 8:
                    device_type = parsed[0]
                    firmware_version = parsed[1]
                    serial_number = struct.unpack('<H', bytes(parsed[2:4]))[0]
                    base_distance = struct.unpack('<H', bytes(parsed[4:6]))[0]
                    sensor_range = struct.unpack('<H', bytes(parsed[6:8]))[0]
                    
                    print(f"📟 Тип устройства: {device_type}")
                    print(f"🔢 Версия ПО: {firmware_version}")
                    print(f"🏷️ Серийный номер: {serial_number}")
                    print(f"📏 Базовое расстояние: {base_distance} мм")
                    print(f"📐 Диапазон: {sensor_range} мм")
                    print(f"📊 Текущий допустимый диапазон: {self.MIN_DISTANCE}-{self.MAX_DISTANCE} мм")
                    print(f"🎯 Целевая частота: {self.TARGET_FREQUENCY} Гц")
                    
                    self.sensor_range = sensor_range
                    self.base_distance = base_distance
                    return True
        except Exception as e:
            print(f"❌ Ошибка идентификации: {e}")
        
        return False

    def set_distance_limits(self):
        """Установка ограничений по расстоянию"""
        print("\n📏 Настройка ограничений по расстоянию")
        print(f"   Максимально возможный диапазон: 80-250 мм")
        print(f"   Текущие значения: {self.MIN_DISTANCE}-{self.MAX_DISTANCE} мм")
        
        while True:
            try:
                min_input = input(f"   Введите минимальное расстояние (по умолчанию {self.MIN_DISTANCE} мм): ").strip()
                if min_input:
                    min_val = float(min_input)
                    if 80 <= min_val <= 250:
                        self.MIN_DISTANCE = min_val
                    else:
                        print("   ❌ Минимальное расстояние должно быть между 80 и 250 мм")
                        continue
                
                max_input = input(f"   Введите максимальное расстояние (по умолчанию {self.MAX_DISTANCE} мм): ").strip()
                if max_input:
                    max_val = float(max_input)
                    if 80 <= max_val <= 250:
                        self.MAX_DISTANCE = max_val
                    else:
                        print("   ❌ Максимальное расстояние должно быть между 80 и 250 мм")
                        continue
                
                if self.MIN_DISTANCE >= self.MAX_DISTANCE:
                    print("   ❌ Минимальное расстояние должно быть меньше максимального")
                    continue
                
                print(f"   ✅ Установлен диапазон: {self.MIN_DISTANCE}-{self.MAX_DISTANCE} мм")
                return True
                
            except ValueError:
                print("   ❌ Пожалуйста, введите числовое значение")
            except KeyboardInterrupt:
                return False

    def plot_measurements(self, filepath):
        """Построение графиков после окончания записи"""
        try:
            # Читаем данные из файла
            distances = []
            point_numbers = []
            timestamps = []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                next(reader)  # Пропускаем заголовок
                for row in reader:
                    if row:  # Проверяем, что строка не пустая
                        distances.append(float(row[0]))
                        point_numbers.append(int(row[1]))
                        timestamps.append(float(row[2]))
            
            if not distances:
                print("❌ Нет данных для построения графиков")
                return
            
            # Автоматическое определение границ графика на основе данных
            data_min = min(distances)
            data_max = max(distances)
            margin = (data_max - data_min) * 0.1  # 10% от диапазона данных
            
            y_min = max(80, data_min - margin)  # Не ниже 80 мм
            y_max = min(250, data_max + margin)  # Не выше 250 мм
            
            # Создаем два графика
            plt.figure(figsize=(15, 6))
            
            # График 1: Расстояние vs Номер точки
            plt.subplot(1, 2, 1)
            plt.plot(point_numbers, distances, 'b-', linewidth=0.5)
            plt.xlabel('Номер точки измерения')
            plt.ylabel('Расстояние (мм)')
            plt.title('Расстояние vs Номер точки')
            plt.grid(True, alpha=0.3)
            plt.ylim(y_min, y_max)
            
            # График 2: Расстояние vs Время
            plt.subplot(1, 2, 2)
            plt.plot(timestamps, distances, 'r-', linewidth=0.5)
            plt.xlabel('Время (сек)')
            plt.ylabel('Расстояние (мм)')
            plt.title('Расстояние vs Время')
            plt.grid(True, alpha=0.3)
            plt.ylim(y_min, y_max)
            
            plt.tight_layout()
            
            # Сохраняем графики в той же папке эксперимента
            plot_filename = os.path.join(os.path.dirname(filepath), 'plot.png')
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            print(f"📊 Графики сохранены как: {plot_filename}")
            
            # Показываем графики
            plt.show()
            
        except Exception as e:
            print(f"❌ Ошибка при построении графиков: {e}")

    def continuous_ultra_fast_logging(self):
        """
        Непрерывная ультра-быстрая запись данных с контролем частоты и таймаутом
        """
        # Переподключаемся перед началом записи
        if not self.reconnect():
            print("❌ Не удалось переподключиться к датчику")
            return False
            
        # Идентифицируем устройство
        if not self.identify_device():
            print("❌ Не удалось идентифицировать устройство")
            self.close()
            return False
        
        # Создаем папку для экспериментов если не существует
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Создаем уникальное имя эксперимента с временной меткой
        experiment_name = f"experiment_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        experiment_dir = self.create_experiment_directory(experiment_name)
        
        # Создаем файл данных в папке эксперимента
        filename = "data.csv"
        filepath = os.path.join(experiment_dir, filename)
        
        print(f"📡 Запуск ультра-быстрой записи...")
        print(f"📁 Папка эксперимента: {experiment_dir}")
        print(f"💾 Файл данных: {filepath}")
        print(f"📊 Допустимый диапазон: {self.MIN_DISTANCE}-{self.MAX_DISTANCE} мм")
        print(f"🎯 Целевая частота: {self.TARGET_FREQUENCY} Гц")
        print(f"⏰ Таймаут: {self.TIMEOUT_DURATION} сек без корректных данных")
        print("🎮 Нажмите Ctrl+C для остановки")
        print("-" * 50)
        
        # Создаем CSV файл с тремя столбцами
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Расстояние_мм', 'Номер_точки', 'Временная_метка'])
        
        self.is_running = True
        start_time = time.perf_counter()
        last_valid_measurement_time = start_time  # Время последнего корректного измерения
        last_print_time = start_time
        measurements_count_since_last_print = 0
        invalid_measurements = 0  # Счетчик некорректных измерений
        
        # Для контроля частоты
        measurement_interval = 1.0 / self.TARGET_FREQUENCY
        
        # Буфер для накопления данных перед записью в файл
        data_buffer = []
        buffer_size = 100  # Размер буфера
        
        timeout_occurred = False
        success = False
        
        try:
            while self.is_running:
                loop_start = time.perf_counter()
                current_time = time.perf_counter()
                
                # Проверка таймаута - если прошло больше 1.5 секунд без корректных данных
                if current_time - last_valid_measurement_time > self.TIMEOUT_DURATION:
                    print(f"❌ ТАЙМАУТ: Нет корректных данных более {self.TIMEOUT_DURATION} секунд!")
                    timeout_occurred = True
                    break
                
                # Получаем измерение
                measurement = self.get_measurement_ultra_fast()
                elapsed_time = current_time - start_time
                
                if measurement is not None:
                    # Обновляем время последнего корректного измерения
                    last_valid_measurement_time = current_time
                    
                    # Добавляем в буфер
                    data_buffer.append([
                        f"{measurement:.3f}", 
                        self.measurement_count, 
                        f"{elapsed_time:.6f}"
                    ])
                    
                    self.measurement_count += 1
                    measurements_count_since_last_print += 1
                    
                    # Записываем в файл при заполнении буфера
                    if len(data_buffer) >= buffer_size:
                        with open(filepath, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f, delimiter=';')
                            writer.writerows(data_buffer)
                        data_buffer = []
                    
                    # Выводим статистику каждые 0.5 секунды
                    if current_time - last_print_time >= 0.5:
                        elapsed = current_time - last_print_time
                        frequency = measurements_count_since_last_print / elapsed
                        print(f"📊 #{self.measurement_count}: {measurement:.3f} мм | Частота: {frequency:.0f} Гц | Отброшено: {invalid_measurements}")
                        last_print_time = current_time
                        measurements_count_since_last_print = 0
                        invalid_measurements = 0
                else:
                    # Увеличиваем счетчик некорректных измерений
                    invalid_measurements += 1
                
                # Контроль частоты - выдерживаем нужный интервал между измерениями
                elapsed_loop = time.perf_counter() - loop_start
                sleep_time = measurement_interval - elapsed_loop
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            print(f"\n⏹ Остановлено пользователем")
            success = True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            # Записываем оставшиеся данные в буфере
            if data_buffer and not timeout_occurred:
                with open(filepath, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerows(data_buffer)
            
            total_time = time.perf_counter() - start_time
            
            if timeout_occurred:
                # Удаляем файл данных при таймауте
                try:
                    os.remove(filepath)
                    print(f"🗑️ Файл данных удален из-за таймаута: {filepath}")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить файл: {e}")
                
                print(f"\n❌ ЗАВЕРШЕНО ПО ТАЙМАУТУ:")
                print(f"   ⏱️ Общее время: {total_time:.1f} сек")
                print(f"   📈 Корректных измерений: {self.measurement_count}")
                print(f"   🚫 Нет корректных данных более {self.TIMEOUT_DURATION} секунд")
                print(f"   🔄 Попробуйте запустить запись заново")
            else:
                avg_frequency = self.measurement_count / total_time if total_time > 0 else 0
                print(f"\n✅ Итоги записи:")
                print(f"   📈 Всего измерений: {self.measurement_count}")
                print(f"   ⏱️ Общее время: {total_time:.1f} сек")
                print(f"   📊 Средняя частота: {avg_frequency:.1f} Гц")
                print(f"   🎯 Целевая частота: {self.TARGET_FREQUENCY} Гц")
                print(f"   📏 Допустимый диапазон: {self.MIN_DISTANCE}-{self.MAX_DISTANCE} мм")
                print(f"   💾 Данные сохранены в: {filepath}")
                
                # Строим графики после окончания записи только если нет таймаута
                if self.measurement_count > 0:
                    print("📊 Строим графики...")
                    self.plot_measurements(filepath)
                    success = True
            
            # Всегда закрываем соединение после операции
            self.close()
            
            # Сбрасываем счетчики для следующей операции
            self.measurement_count = 0
            
            return success

    def test_performance(self):
        """Тест производительности с автоматическим переподключением"""
        # Переподключаемся перед началом теста
        if not self.reconnect():
            print("❌ Не удалось переподключиться к датчику")
            return False
            
        # Идентифицируем устройство
        if not self.identify_device():
            print("❌ Не удалось идентифицировать устройство")
            self.close()
            return False
            
        print("🚀 Тест производительности...")
        test_duration = 5
        print(f"Измеряем максимальную скорость в течение {test_duration} секунд...")
        print(f"Учитываются только измерения {self.MIN_DISTANCE}-{self.MAX_DISTANCE} мм")
        print(f"Целевая частота: {self.TARGET_FREQUENCY} Гц")
        
        start_time = time.perf_counter()
        count = 0
        invalid_count = 0
        
        # Для контроля частоты в тесте
        measurement_interval = 1.0 / self.TARGET_FREQUENCY
        
        try:
            while time.perf_counter() - start_time < test_duration:
                loop_start = time.perf_counter()
                
                measurement = self.get_measurement_ultra_fast()
                if measurement is not None:
                    count += 1
                else:
                    invalid_count += 1
                
                # Контроль частоты
                elapsed_loop = time.perf_counter() - loop_start
                sleep_time = measurement_interval - elapsed_loop
                if sleep_time > 0:
                    time.sleep(sleep_time)
        except Exception as e:
            print(f"❌ Ошибка во время теста: {e}")
        finally:
            total_time = time.perf_counter() - start_time
            frequency = count / total_time
            print(f"📊 Результаты теста:")
            print(f"   ✅ Корректных измерений: {count}")
            print(f"   ❌ Некорректных измерений: {invalid_count}")
            print(f"   ⏱️ Время: {total_time:.2f} сек")
            print(f"   📊 Частота корректных данных: {frequency:.1f} Гц")
            print(f"   🎯 Целевая частота: {self.TARGET_FREQUENCY} Гц")
            
            # Закрываем соединение после теста
            self.close()
            
            return count > 0

def select_port():
    """Ручной выбор COM-порта"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("❌ COM-порты не найдены!")
        return None
    
    print("\n📡 Найденные порты:")
    for i, port in enumerate(ports):
        print(f"   {i+1}. {port.device} - {port.description}")
    
    while True:
        try:
            choice = input(f"\n🎯 Выберите порт (1-{len(ports)}): ").strip()
            if choice.isdigit():
                port_index = int(choice) - 1
                if 0 <= port_index < len(ports):
                    selected_port = ports[port_index].device
                    print(f"✅ Выбран порт: {selected_port}")
                    return selected_port
            print("❌ Неверный выбор. Попробуйте снова.")
        except KeyboardInterrupt:
            return None

def select_baudrate():
    """Ручной выбор скорости передачи с 921600 по умолчанию"""
    baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
    default_baudrate = 921600
    
    print("\n⚡ Доступные скорости передачи:")
    for i, baud in enumerate(baudrates):
        default_mark = " (по умолчанию)" if baud == default_baudrate else ""
        print(f"   {i+1}. {baud}{default_mark}")
    
    while True:
        try:
            choice = input(f"\n🎯 Выберите скорость (1-{len(baudrates)}, Enter для {default_baudrate}): ").strip()
            if not choice:  # Пустой ввод - используем по умолчанию
                print(f"✅ Используется скорость по умолчанию: {default_baudrate}")
                return default_baudrate
            elif choice.isdigit():
                baud_index = int(choice) - 1
                if 0 <= baud_index < len(baudrates):
                    selected_baudrate = baudrates[baud_index]
                    print(f"✅ Выбрана скорость: {selected_baudrate}")
                    return selected_baudrate
            print("❌ Неверный выбор. Попробуйте снова.")
        except KeyboardInterrupt:
            return None

def main():
    print("РФ603 Ultra-Fast Data Logger - Улучшенная версия")
    print("=" * 60)
    
    logger = RF603UltraFastLogger()
    
    # Выбор порта
    selected_port = select_port()
    if not selected_port:
        return
    
    # Выбор скорости (по умолчанию 921600)
    selected_baudrate = select_baudrate()
    if not selected_baudrate:
        return
    
    # Сохраняем выбранные настройки
    logger.selected_port = selected_port
    logger.selected_baudrate = selected_baudrate
    
    # Запрашиваем ограничения по расстоянию
    if not logger.set_distance_limits():
        return
    
    while True:
        print("\n" + "="*50)
        print("Выберите действие:")
        print("1. 🚀 Запуск ультра-быстрой записи (2000 Гц)")
        print("2. 📊 Тест производительности (5 сек)")
        print("3. 📏 Изменить ограничения по расстоянию")
        print("4. ❌ Выход")
        
        choice = input("Ваш выбор (1-4): ").strip()
        
        if choice == '1':
            # Запускаем ультра-быструю запись
            success = logger.continuous_ultra_fast_logging()
            if not success:
                print("❌ Запись завершилась с ошибкой. Устройство перезапущено.")
            else:
                print("✅ Запись завершена успешно. Устройство перезапущено.")
                
        elif choice == '2':
            # Тест производительности
            success = logger.test_performance()
            if not success:
                print("❌ Тест завершился с ошибкой. Устройство перезапущено.")
            else:
                print("✅ Тест завершен успешно. Устройство перезапущено.")
                        
        elif choice == '3':
            # Изменение ограничений по расстоянию
            logger.set_distance_limits()
            
        elif choice == '4':
            break
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
