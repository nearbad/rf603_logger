# -*- coding: utf-8 -*-
"""
Скрипт для визуализации данных с датчика RF603HS в реальном времени
"""

import serial
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
from datetime import datetime
import csv
import pandas as pd

class RF603RealtimePlotter:
    """Класс для визуализации данных в реальном времени"""

    def __init__(self, max_points=1000):
        self.max_points = max_points
        self.time_data = deque(maxlen=max_points)
        self.distance_data = deque(maxlen=max_points)
        self.point_counter = 0
        self.start_time = None
        self.serial_port = None
        self.is_running = False

        # CSV файл
        self.csv_file = None
        self.csv_writer = None

        # Настройка графиков
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.line1, = self.ax1.plot([], [], 'b-', linewidth=1.5, label='Расстояние (мм)')
        self.line2, = self.ax2.plot([], [], 'r-', linewidth=1.5, label='Точки')

        # Настройка осей
        self.ax1.set_xlabel('Время (сек)', fontsize=12)
        self.ax1.set_ylabel('Расстояние (мм)', fontsize=12)
        self.ax1.set_title('Данные с датчика RF603HS в реальном времени', fontsize=14, fontweight='bold')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend()

        self.ax2.set_xlabel('Номер точки', fontsize=12)
        self.ax2.set_ylabel('Расстояние (мм)', fontsize=12)
        self.ax2.set_title('Зависимость расстояния от номера точки', fontsize=14, fontweight='bold')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend()

        plt.tight_layout()

        # Информационный текст
        self.info_text = self.ax1.text(0.02, 0.98, '', transform=self.ax1.transAxes,
                                       verticalalignment='top',
                                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                                       fontsize=10)

    def connect(self, port, baudrate=9600):
        """Подключение к датчику"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5
            )

            time.sleep(0.5)
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

            # Идентификация
            if self.identify_device():
                print("✅ Подключено к датчику")
                return True

            return False

        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def identify_device(self):
        """Идентификация датчика"""
        try:
            # Запрос идентификации (01h)
            request = bytes([0x01, 0x81])
            self.serial_port.write(request)
            time.sleep(0.1)

            response = self.serial_port.read(16)

            if len(response) >= 16:
                # Декодируем базовое расстояние и диапазон
                base_dist_low = (response[8] & 0x0F) | ((response[9] & 0x0F) << 4)
                base_dist_high = (response[10] & 0x0F) | ((response[11] & 0x0F) << 4)
                self.base_distance = (base_dist_high << 8) | base_dist_low

                range_low = (response[12] & 0x0F) | ((response[13] & 0x0F) << 4)
                range_high = (response[14] & 0x0F) | ((response[15] & 0x0F) << 4)
                self.measurement_range = (range_high << 8) | range_low

                print(f"📊 Базовое расстояние: {self.base_distance} мм")
                print(f"📊 Диапазон: {self.measurement_range} мм")

                return True

            return False

        except Exception as e:
            print(f"❌ Ошибка идентификации: {e}")
            return False

    def start_stream(self):
        """Запуск потока данных"""
        try:
            request = bytes([0x01, 0x87])  # Запрос 07h
            self.serial_port.write(request)
            print("📡 Поток данных запущен")
        except Exception as e:
            print(f"❌ Ошибка запуска потока: {e}")

    def stop_stream(self):
        """Остановка потока данных"""
        try:
            request = bytes([0x01, 0x88])  # Запрос 08h
            self.serial_port.write(request)
            print("⏹ Поток данных остановлен")
        except Exception as e:
            print(f"❌ Ошибка остановки потока: {e}")

    def read_measurement(self):
        """Чтение одного измерения"""
        try:
            if self.serial_port.in_waiting >= 4:
                data = self.serial_port.read(4)

                if len(data) == 4 and (data[0] & 0x80) and (data[2] & 0x80):
                    # Декодируем
                    low_byte = (data[0] & 0x0F) | ((data[1] & 0x0F) << 4)
                    high_byte = (data[2] & 0x0F) | ((data[3] & 0x0F) << 4)
                    raw_value = (high_byte << 8) | low_byte

                    # Преобразуем в мм
                    distance_mm = (raw_value * self.measurement_range) / 0x4000

                    return distance_mm

            return None

        except Exception as e:
            return None

    def open_csv(self, filename=None):
        """Открыть CSV файл для записи"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rf603_realtime_{timestamp}.csv"

        self.csv_filename = filename
        self.csv_file = open(filename, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file, delimiter=';')
        self.csv_writer.writerow(['Расстояние_мм', 'Номер_точки', 'Временная_метка'])

        print(f"📁 CSV файл создан: {filename}")

    def close_csv(self):
        """Закрыть CSV файл"""
        if self.csv_file:
            self.csv_file.close()
            print(f"✅ Данные сохранены в {self.csv_filename}")

    def update_plot(self, frame):
        """Обновление графиков"""
        distance = self.read_measurement()

        if distance is not None:
            if self.start_time is None:
                self.start_time = time.time()

            elapsed_time = time.time() - self.start_time
            self.time_data.append(elapsed_time)
            self.distance_data.append(distance)

            # Записываем в CSV
            if self.csv_writer:
                self.csv_writer.writerow([distance, self.point_counter, elapsed_time])

            self.point_counter += 1

            # Обновляем графики
            if len(self.time_data) > 1:
                # График 1: время - расстояние
                self.line1.set_data(list(self.time_data), list(self.distance_data))
                self.ax1.relim()
                self.ax1.autoscale_view()

                # График 2: точки - расстояние
                points = list(range(max(0, self.point_counter - len(self.distance_data)),
                                   self.point_counter))
                self.line2.set_data(points, list(self.distance_data))
                self.ax2.relim()
                self.ax2.autoscale_view()

                # Обновляем информацию
                if len(self.distance_data) >= 2:
                    current_dist = self.distance_data[-1]
                    min_dist = min(self.distance_data)
                    max_dist = max(self.distance_data)
                    avg_dist = np.mean(self.distance_data)

                    info = f'Точек: {self.point_counter}\n'
                    info += f'Время: {elapsed_time:.2f} сек\n'
                    info += f'Текущее: {current_dist:.3f} мм\n'
                    info += f'Мин: {min_dist:.3f} мм\n'
                    info += f'Макс: {max_dist:.3f} мм\n'
                    info += f'Среднее: {avg_dist:.3f} мм'

                    self.info_text.set_text(info)

        return self.line1, self.line2, self.info_text

    def run(self):
        """Запуск визуализации"""
        self.is_running = True
        self.start_stream()
        self.open_csv()

        # Создаем анимацию
        ani = animation.FuncAnimation(
            self.fig,
            self.update_plot,
            interval=10,  # 10 мс между обновлениями
            blit=False,
            cache_frame_data=False
        )

        plt.show()

        # После закрытия окна
        self.stop_stream()
        self.close_csv()
        self.is_running = False

        if self.serial_port:
            self.serial_port.close()

        print("✅ Визуализация завершена")

        return self.csv_filename


def main():
    """Главная функция"""
    print("="*70)
    print(" "*10 + "RF603HS REALTIME VISUALIZATION")
    print("="*70)

    # Список портов
    ports = serial.tools.list_ports.comports()
    available_ports = []

    print("\nДоступные порты:")
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device} - {port.description}")
        available_ports.append(port.device)

    if not available_ports:
        print("❌ Нет доступных портов")
        return

    # Выбор порта
    try:
        port_choice = int(input(f"\nВыберите порт (1-{len(available_ports)}): ")) - 1
        selected_port = available_ports[port_choice]
    except (ValueError, IndexError):
        print("❌ Неверный выбор")
        return

    # Выбор скорости
    print("\nСкорость (бод):")
    print("1. 9600 (по умолчанию)")
    print("2. 19200")
    print("3. 57600")
    print("4. 115200")

    baud_rates = {1: 9600, 2: 19200, 3: 57600, 4: 115200}
    try:
        baud_choice = int(input("Выберите (1-4): "))
        selected_baud = baud_rates.get(baud_choice, 9600)
    except ValueError:
        selected_baud = 9600

    # Создаем визуализатор
    plotter = RF603RealtimePlotter(max_points=1000)

    if not plotter.connect(selected_port, selected_baud):
        print("❌ Не удалось подключиться")
        return

    print("\n" + "="*70)
    print("НАЧАЛО ВИЗУАЛИЗАЦИИ")
    print("="*70)
    print("Закройте окно графика для остановки")
    print("="*70)

    # Запускаем
    csv_file = plotter.run()

    # Предлагаем анализ
    if csv_file:
        print("\n" + "="*70)
        print("АНАЛИЗ ДАННЫХ")
        print("="*70)
        analyze = input("Выполнить автоматический анализ? (y/n): ").lower()

        if analyze == 'y':
            from rf603_logger import RF603OscillationAnalyzer

            analyzer = RF603OscillationAnalyzer()
            if analyzer.load_csv(csv_file):
                analyzer.normalize_data()

                duration = float(input("Длительность анализа после начала (сек) [1.0]: ") or "1.0")
                success, period, freq, peaks = analyzer.auto_crop_oscillations(duration)

                if success:
                    print(f"\n⏱️ Период: {period:.6f} сек")
                    print(f"📊 Частота: {freq:.2f} Гц")

                    if analyzer.log_decrement:
                        print(f"📉 Логарифмический декремент: {analyzer.log_decrement:.6f}")
                        print(f"📉 Коэффициент потерь: {analyzer.loss_factor:.6f}")

                    analyzer.plot_results()

    print("\n✅ Программа завершена!")


if __name__ == "__main__":
    main()
