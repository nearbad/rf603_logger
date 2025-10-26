# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.signal import find_peaks, savgol_filter, argrelextrema
import tkinter as tk
from tkinter import filedialog, messagebox
from scipy.optimize import curve_fit

class RF603OscillationAnalyzer:
    def __init__(self):
        self.data = None
        self.processed_data = None
        self.original_processed_data = None
        self.oscillation_start = 0
        self.oscillation_end = 0
        self.corrected_peaks = None
        self.current_period = None
        self.current_frequency = None
        self.log_decrement = None  # Логарифмический декремент
        self.loss_factor = None   # Коэффициент потерь
        self.damping_ratio = None # Коэффициент демпфирования
        
    def load_csv(self, filename):
        """Загрузка CSV файла с данными"""
        try:
            self.data = pd.read_csv(filename, delimiter=';', encoding='utf-8')
            print(f"✅ Данные загружены из: {filename}")
            print(f"📊 Загружено {len(self.data)} строк")
            print(f"📏 Диапазон расстояний: {self.data['Расстояние_мм'].min():.3f} - {self.data['Расстояние_мм'].max():.3f} мм")
            print(f"⏱️ Общее время: {self.data['Временная_метка'].iloc[-1]:.3f} сек")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки файла: {e}")
            return False
    
    def normalize_data(self):
        """Нормировка данных - вычитание первого значения"""
        if self.data is None:
            print("❌ Нет данных для обработки")
            return False
            
        try:
            self.processed_data = self.data.copy()
            
            # 1. Вычитаем первое значение из всех расстояний
            first_distance = self.processed_data.iloc[0]['Расстояние_мм']
            self.processed_data['Расстояние_норм'] = (
                self.processed_data['Расстояние_мм'] - first_distance
            )
            
            # Сохраняем исходные нормированные данные
            self.original_processed_data = self.processed_data.copy()
            
            # Сбрасываем исправленные пики при нормировке
            self.corrected_peaks = None
            self.current_period = None
            self.current_frequency = None
            self.log_decrement = None
            self.loss_factor = None
            self.damping_ratio = None
            
            print(f"✅ Нормировка выполнена. Первое значение: {first_distance:.3f} мм")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка нормировки данных: {e}")
            return False

    def reset_to_original(self):
        """Сброс к исходным нормированным данным"""
        if self.original_processed_data is not None:
            self.processed_data = self.original_processed_data.copy()
            self.oscillation_start = 0
            self.oscillation_end = len(self.processed_data) - 1
            
            # СБРАСЫВАЕМ исправленные пики при сбросе данных
            self.corrected_peaks = None
            self.current_period = None
            self.current_frequency = None
            self.log_decrement = None
            self.loss_factor = None
            self.damping_ratio = None
            
            print("✅ Данные сброшены к исходным нормированным")
            return True
        else:
            print("❌ Нет исходных данных для сброса")
            return False

    def crop_by_time(self, start_time, end_time):
        """Обрезка данных по времени"""
        if self.processed_data is None:
            print("❌ Нет обработанных данных")
            return False
            
        try:
            # Находим индексы по времени
            start_mask = self.processed_data['Временная_метка'] >= start_time
            end_mask = self.processed_data['Временная_метка'] <= end_time
            
            if not any(start_mask) or not any(end_mask):
                print("❌ Указанные временные границы вне диапазона данных")
                return False
                
            start_idx = self.processed_data[start_mask].index[0]
            end_idx = self.processed_data[end_mask].index[-1]
            
            return self.crop_by_points(start_idx, end_idx)
            
        except Exception as e:
            print(f"❌ Ошибка обрезки по времени: {e}")
            return False

    def crop_by_points(self, start_point, end_point):
        """Обрезка данных по точкам"""
        if self.processed_data is None:
            print("❌ Нет обработанных данных")
            return False
            
        try:
            start_idx = max(0, min(start_point, len(self.processed_data) - 1))
            end_idx = max(start_idx + 1, min(end_point, len(self.processed_data) - 1))
            
            original_count = len(self.processed_data)
            self.processed_data = self.processed_data.iloc[start_idx:end_idx + 1].reset_index(drop=True)
            self.oscillation_start = start_idx
            self.oscillation_end = end_idx
            
            # Сбрасываем исправленные пики при обрезке данных
            self.corrected_peaks = None
            self.current_period = None
            self.current_frequency = None
            self.log_decrement = None
            self.loss_factor = None
            self.damping_ratio = None
            
            print(f"✅ Данные обрезаны:")
            print(f"   📍 Точки: {start_idx}-{end_idx}")
            print(f"   ⏱️ Время: {self.processed_data['Временная_метка'].iloc[0]:.3f}-{self.processed_data['Временная_метка'].iloc[-1]:.3f} сек")
            print(f"   📊 Точек до: {original_count}")
            print(f"   📊 Точек после: {len(self.processed_data)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обрезки по точкам: {e}")
            return False

    def find_release_point(self, threshold=0.5):
        """
        Нахождение момента отпускания объекта
        Ищем резкое изменение расстояния (начало колебаний)
        """
        if self.processed_data is None:
            return 0
            
        distances = self.processed_data['Расстояние_норм'].values
        
        # Ищем точку, где расстояние резко изменилось
        for i in range(1, len(distances) - 10):
            # Проверяем изменение на следующем участке
            window = distances[i:i+10]
            if np.max(window) - np.min(window) > threshold:
                release_point = max(0, i - 5)  # Немного отступаем назад
                print(f"📍 Начало колебаний найдено в точке {release_point}")
                return release_point
        
        print("⚠️ Не удалось найти начало колебаний автоматически")
        return 0

    def auto_crop_oscillations(self, duration_after_start=1.0):
        """
        Автоматическое определение начала колебаний и обрезка данных
        duration_after_start: продолжительность данных после начала колебаний (в секундах)
        """
        if self.processed_data is None:
            print("❌ Нет обработанных данных")
            return False, None, None, None
            
        try:
            # Сначала сбрасываем к исходным данным
            self.reset_to_original()
            
            # Находим начало колебаний
            start_idx = self.find_release_point(threshold=0.5)
            if start_idx == 0:
                print("❌ Не удалось найти начало колебаний")
                return False, None, None, None
            
            # Получаем временную метку начала колебаний
            start_time = self.processed_data.iloc[start_idx]['Временная_метка']
            end_time = start_time + duration_after_start
            
            print(f"📍 Начало колебаний: {start_time:.3f} сек")
            print(f"📍 Конец обрезки: {end_time:.3f} сек")
            print(f"⏱️ Длительность анализа: {duration_after_start} сек")
            
            # Обрезаем данные от начала колебаний до start_time + duration_after_start
            if not self.crop_by_time(start_time, end_time):
                print("❌ Ошибка при обрезке данных по времени")
                return False, None, None, None
            
            # Сразу рассчитываем период и частоту
            period, frequency, peaks = self.calculate_period_frequency_improved()
            
            return True, period, frequency, peaks
            
        except Exception as e:
            print(f"❌ Ошибка автоматической обрезки: {e}")
            return False, None, None, None

    def calculate_logarithmic_decrement(self, peaks):
        """
        Расчет логарифмического декремента затухания и коэффициента потерь
        согласно методике из диссертации (раздел 3.2)
        """
        if peaks is None or len(peaks) < 2:
            print("❌ Недостаточно пиков для расчета логарифмического декремента")
            return None, None, None
            
        try:
            distances = self.processed_data['Расстояние_норм'].values
            timestamps = self.processed_data['Временная_метка'].values
            
            # Получаем амплитуды в пиках
            amplitudes = distances[peaks]
            
            # Рассчитываем логарифмический декремент для каждой пары последовательных пиков
            decrements = []
            for i in range(len(peaks) - 1):
                A_i = abs(amplitudes[i])
                A_i_plus_1 = abs(amplitudes[i + 1])
                
                if A_i_plus_1 > 0:  # Избегаем деления на ноль
                    delta = np.log(A_i / A_i_plus_1)
                    decrements.append(delta)
            
            if not decrements:
                print("❌ Не удалось рассчитать логарифмический декремент")
                return None, None, None
            
            # Средний логарифмический декремент
            avg_decrement = np.mean(decrements)
            
            # Коэффициент демпфирования (формула 3.2 из диссертации)
            damping_ratio = avg_decrement / np.sqrt(4 * np.pi**2 + avg_decrement**2)
            
            # Коэффициент потерь (формула 3.3 из диссертации)
            loss_factor = 2 * damping_ratio
            
            print(f"📉 Логарифмический декремент (δ): {avg_decrement:.6f}")
            print(f"📉 Коэффициент демпфирования (ζ): {damping_ratio:.6f}")
            print(f"📉 Коэффициент потерь (η): {loss_factor:.6f}")
            print(f"📊 Использовано пар пиков: {len(decrements)}")
            
            # Сохраняем результаты
            self.log_decrement = avg_decrement
            self.damping_ratio = damping_ratio
            self.loss_factor = loss_factor
            
            return avg_decrement, damping_ratio, loss_factor
            
        except Exception as e:
            print(f"❌ Ошибка расчета логарифмического декремента: {e}")
            return None, None, None

    def calculate_period_frequency_improved(self):
        """
        УЛУЧШЕННЫЙ расчет периода и частоты с адаптивными параметрами
        """
        if self.processed_data is None:
            print("❌ Нет данных для анализа")
            return None, None, None
            
        try:
            distances = self.processed_data['Расстояние_норм'].values
            timestamps = self.processed_data['Временная_метка'].values
            
            # Если есть исправленные пики, используем их
            if self.corrected_peaks is not None and len(self.corrected_peaks) >= 2:
                print("📊 Используются исправленные пики")
                peaks = self.corrected_peaks
            else:
                # Иначе ищем пики автоматически
                # Применяем фильтр для сглаживания шумов
                if len(distances) > 11:
                    distances_smooth = savgol_filter(distances, 11, 3)
                else:
                    distances_smooth = distances
                
                # АДАПТИВНОЕ определение параметров поиска пиков
                amplitude = np.max(distances_smooth) - np.min(distances_smooth)
                
                # Пробуем несколько стратегий поиска пиков
                peaks = self._find_peaks_adaptive(distances_smooth, amplitude)
            
            if len(peaks) < 2:
                print("❌ Не найдено достаточно пиков для анализа")
                return None, None, None
            
            print(f"📈 Найдено пиков: {len(peaks)}")
            
            # Рассчитываем периоды между последовательными пиками
            periods = []
            for i in range(len(peaks) - 1):
                period = timestamps[peaks[i + 1]] - timestamps[peaks[i]]
                periods.append(period)
                print(f"   Период {i+1}: {period:.6f} сек")
            
            # УЛУЧШЕННАЯ фильтрация выбросов
            if len(periods) >= 3:
                # Используем межквартильный размах для фильтрации выбросов
                Q1 = np.percentile(periods, 25)
                Q3 = np.percentile(periods, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                filtered_periods = [p for p in periods if lower_bound <= p <= upper_bound]
            else:
                filtered_periods = periods
            
            if not filtered_periods:
                print("⚠️ Все периоды отфильтрованы как выбросы, используем исходные")
                filtered_periods = periods
                
            # Рассчитываем средний период и частоту
            avg_period = np.mean(filtered_periods)
            frequency = 1.0 / avg_period if avg_period > 0 else 0
            
            # Сохраняем текущие значения
            self.current_period = avg_period
            self.current_frequency = frequency
            
            print(f"⏱️ Средний период: {avg_period:.6f} сек")
            print(f"📊 Частота: {frequency:.2f} Гц")
            print(f"📊 Использовано периодов: {len(filtered_periods)} из {len(periods)}")
            
            # РАСЧЕТ ЛОГАРИФМИЧЕСКОГО ДЕКРЕМЕНТА
            self.calculate_logarithmic_decrement(peaks)
            
            return avg_period, frequency, peaks
            
        except Exception as e:
            print(f"❌ Ошибка расчета параметров: {e}")
            return None, None, None

    def _find_peaks_adaptive(self, signal, amplitude):
        """
        Адаптивный поиск пиков с несколькими стратегиями
        """
        # Стратегия 1: стандартный поиск пиков
        try:
            peaks, properties = find_peaks(
                signal,
                height=amplitude * 0.1,  # Адаптивная высота
                distance=max(3, len(signal) // 20),  # Адаптивное расстояние
                prominence=amplitude * 0.05,  # Адаптивная выступаемость
                width=2
            )
            
            if len(peaks) >= 3:
                print("✅ Использована стратегия 1 (стандартная)")
                return peaks
        except:
            pass
        
        # Стратегия 2: поиск локальных максимумов
        try:
            # Используем относительные экстремумы
            peaks = argrelextrema(signal, np.greater, order=3)[0]
            
            if len(peaks) >= 3:
                print("✅ Использована стратегия 2 (локальные максимумы)")
                return peaks
        except:
            pass
        
        # Стратегия 3: менее строгие параметры
        try:
            peaks, properties = find_peaks(
                signal,
                height=amplitude * 0.05,
                distance=2,
                prominence=amplitude * 0.02
            )
            
            if len(peaks) >= 2:
                print("✅ Использована стратегия 3 (менее строгая)")
                return peaks
        except:
            pass
        
        # Стратегия 4: поиск по производной (переход через ноль второй производной)
        try:
            # Вычисляем первую и вторую производные
            first_derivative = np.gradient(signal)
            second_derivative = np.gradient(first_derivative)
            
            # Ищем точки перегиба (где вторая производная меняет знак)
            inflection_points = []
            for i in range(1, len(second_derivative)):
                if (second_derivative[i-1] * second_derivative[i] < 0 and 
                    second_derivative[i-1] > 0):  # Только вогнутость -> выпуклость
                    inflection_points.append(i)
            
            if len(inflection_points) >= 2:
                print("✅ Использована стратегия 4 (по производной)")
                return np.array(inflection_points)
        except:
            pass
        
        print("❌ Не удалось найти пики ни одной стратегией")
        return np.array([])

    def manual_peak_correction(self, current_peaks):
        """
        Ручная коррекция пиков через графический интерфейс - ИСПРАВЛЕННАЯ ВЕРСИЯ
        """
        if self.processed_data is None or current_peaks is None:
            return current_peaks
            
        print("\n🔧 Режим ручной коррекции пиков")
        print("   Добавьте пики: щелкните левой кнопкой")
        print("   Удалите пики: щелкните правой кнопкой")
        print("   Завершите: нажмите Enter")
        
        time_processed = self.processed_data['Временная_метка']
        distance_processed = self.processed_data['Расстояние_норм']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Основной график данных
        ax.plot(time_processed, distance_processed, 'b-', linewidth=1.5, label='Данные')
        
        # Создаем отдельный объект для отображения пиков
        peak_points, = ax.plot(time_processed.iloc[current_peaks], distance_processed.iloc[current_peaks], 
                'ro', markersize=8, label='Текущие пики')
        
        ax.set_xlabel('Время (сек)')
        ax.set_ylabel('Нормированное расстояние (мм)')
        ax.set_title('Ручная коррекция пиков - ЛКМ: добавить, ПКМ: удалить, Enter: завершить')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        corrected_peaks = list(current_peaks.copy())
        
        def update_peaks_display():
            """Обновляет отображение пиков на графике"""
            peak_points.set_data(time_processed.iloc[corrected_peaks], distance_processed.iloc[corrected_peaks])
            fig.canvas.draw_idle()
        
        def on_click(event):
            if event.inaxes == ax:
                if event.button == 1:  # Левая кнопка - добавление пика
                    # Находим ближайшую точку данных
                    x_click = event.xdata
                    
                    # Ищем ближайшую точку по времени
                    time_diffs = np.abs(time_processed - x_click)
                    closest_idx = time_diffs.idxmin()
                    
                    if closest_idx not in corrected_peaks:
                        corrected_peaks.append(closest_idx)
                        corrected_peaks.sort()  # Сортируем для порядка
                        update_peaks_display()
                        print(f"✅ Добавлен пик в точке {closest_idx}")
                
                elif event.button == 3:  # Правая кнопка - удаление пика
                    x_click = event.xdata
                    
                    # Находим ближайший пик
                    if corrected_peaks:
                        peak_times = time_processed.iloc[corrected_peaks]
                        time_diffs = np.abs(peak_times - x_click)
                        closest_peak_idx_in_list = time_diffs.argmin()
                        removed_peak = corrected_peaks[closest_peak_idx_in_list]
                        
                        corrected_peaks.remove(removed_peak)
                        update_peaks_display()
                        print(f"❌ Удален пик в точке {removed_peak}")
        
        def on_key(event):
            if event.key == 'enter':
                plt.close()
        
        fig.canvas.mpl_connect('button_press_event', on_click)
        fig.canvas.mpl_connect('key_press_event', on_key)
        
        plt.show()
        
        # Сортируем пики по времени
        corrected_peaks = sorted(corrected_peaks)
        print(f"📊 Итоговое количество пиков: {len(corrected_peaks)}")
        
        # СОХРАНЯЕМ исправленные пики в атрибут класса
        self.corrected_peaks = np.array(corrected_peaks)
        
        return np.array(corrected_peaks)

    def plot_raw_data(self):
        """Построение графика необработанных данных"""
        if self.data is None:
            print("❌ Нет данных для построения графика")
            return
            
        try:
            plt.figure(figsize=(12, 6))
            
            plt.plot(self.data['Временная_метка'], self.data['Расстояние_мм'], 
                    'b-', linewidth=1, label='Исходные данные')
            
            plt.xlabel('Время (сек)')
            plt.ylabel('Расстояние (мм)')
            plt.title('Необработанные данные РФ603')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"❌ Ошибка построения графика: {e}")

    def plot_processed_data(self, period=None, frequency=None, peaks=None):
        """Построение графика обработанных данных"""
        if self.processed_data is None:
            print("❌ Нет обработанных данных")
            return
            
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # График 1: Исходные и обработанные данные
            ax1.plot(self.data['Временная_метка'], self.data['Расстояние_мм'], 
                    'gray', alpha=0.5, linewidth=1, label='Все данные')
            
            if len(self.processed_data) > 0:
                oscillation_times = self.processed_data['Временная_метка']
                oscillation_distances = self.processed_data['Расстояние_мм']
                ax1.plot(oscillation_times, oscillation_distances, 'b-', linewidth=2, label='Обрезанные данные')
                
                # Отмечаем границы
                start_time = oscillation_times.iloc[0]
                end_time = oscillation_times.iloc[-1]
                ax1.axvline(x=start_time, color='g', linestyle='--', alpha=0.7, label='Начало')
                ax1.axvline(x=end_time, color='r', linestyle='--', alpha=0.7, label='Конец')
            
            ax1.set_xlabel('Время (сек)')
            ax1.set_ylabel('Расстояние (мм)')
            ax1.set_title('Сравнение исходных и обрезанных данных')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # График 2: Нормированные данные
            if len(self.processed_data) > 0:
                time_processed = self.processed_data['Временная_метка']
                distance_processed = self.processed_data['Расстояние_норм']
                
                ax2.plot(time_processed, distance_processed, 'g-', linewidth=1.5, label='Нормированное расстояние')
                
                # ИСПОЛЬЗУЕМ исправленные пики если они есть, иначе переданные
                display_peaks = self.corrected_peaks if self.corrected_peaks is not None else peaks
                
                if display_peaks is not None and len(display_peaks) > 0:
                    ax2.plot(time_processed.iloc[display_peaks], distance_processed.iloc[display_peaks], 
                            'ro', markersize=6, label='Пики', alpha=0.7)
                
                # ИСПОЛЬЗУЕМ текущие период и частоту если они есть
                display_period = self.current_period if self.current_period is not None else period
                display_frequency = self.current_frequency if self.current_frequency is not None else frequency
                
                # Добавляем информацию о периоде и частоте
                info_text = ''
                if display_period is not None and display_frequency is not None:
                    info_text = f'Период: {display_period:.6f} сек\nЧастота: {display_frequency:.2f} Гц'
                
                # Добавляем информацию о логарифмическом декременте и коэффициенте потерь
                if self.log_decrement is not None and self.loss_factor is not None:
                    info_text += f'\nЛог. декремент (δ): {self.log_decrement:.6f}'
                    info_text += f'\nКоэф. потерь (η): {self.loss_factor:.6f}'
                
                if self.corrected_peaks is not None:
                    info_text += '\n(исправленные пики)'
                
                if info_text:
                    ax2.text(0.02, 0.98, info_text, 
                            transform=ax2.transAxes, verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                            fontsize=10)
                
                ax2.set_xlabel('Время (сек)')
                ax2.set_ylabel('Нормированное расстояние (мм)')
                ax2.set_title('Анализ затухающих колебаний')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"❌ Ошибка построения графика: {e}")

    def plot_detailed_analysis(self, period=None, frequency=None, peaks=None):
        """Детальный анализ с периодами между пиками"""
        if self.processed_data is None:
            print("❌ Нет обработанных данных")
            return
            
        try:
            time_processed = self.processed_data['Временная_метка']
            distance_processed = self.processed_data['Расстояние_норм']
            
            plt.figure(figsize=(12, 6))
            plt.plot(time_processed, distance_processed, 'b-', linewidth=1.5, label='Нормированное расстояние')
            
            # ИСПОЛЬЗУЕМ исправленные пики если они есть, иначе переданные
            display_peaks = self.corrected_peaks if self.corrected_peaks is not None else peaks
            
            if display_peaks is not None and len(display_peaks) > 1:
                plt.plot(time_processed.iloc[display_peaks], distance_processed.iloc[display_peaks], 
                        'ro', markersize=6, label='Пики')
                
                # Рассчитываем и отображаем периоды между пиками
                for i in range(len(display_peaks) - 1):
                    period_val = time_processed.iloc[display_peaks[i+1]] - time_processed.iloc[display_peaks[i]]
                    mid_time = (time_processed.iloc[display_peaks[i]] + time_processed.iloc[display_peaks[i+1]]) / 2
                    mid_val = (distance_processed.iloc[display_peaks[i]] + distance_processed.iloc[display_peaks[i+1]]) / 2
                    
                    plt.annotate(f'T={period_val:.4f}s', 
                               xy=(mid_time, mid_val),
                               xytext=(0, 20), textcoords='offset points',
                               ha='center', va='bottom',
                               bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7),
                               arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            
            # ИСПОЛЬЗУЕМ текущие период и частоту если они есть
            display_period = self.current_period if self.current_period is not None else period
            display_frequency = self.current_frequency if self.current_frequency is not None else frequency
            
            info_text = ''
            if display_period is not None and display_frequency is not None:
                info_text = f'Средний период: {display_period:.6f} сек\nЧастота: {display_frequency:.2f} Гц'
            
            # Добавляем информацию о логарифмическом декременте и коэффициенте потерь
            if self.log_decrement is not None and self.loss_factor is not None:
                info_text += f'\nЛог. декремент (δ): {self.log_decrement:.6f}'
                info_text += f'\nКоэф. потерь (η): {self.loss_factor:.6f}'
            
            if self.corrected_peaks is not None:
                info_text += '\n(исправленные пики)'
            
            if info_text:
                plt.text(0.02, 0.98, info_text, 
                        transform=plt.gca().transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.xlabel('Время (сек)')
            plt.ylabel('Нормированное расстояние (мм)')
            plt.title('Детальный анализ периодов колебаний')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"❌ Ошибка построения детального графика: {e}")

    def plot_logarithmic_decrement_analysis(self):
        """
        Специальный график для анализа логарифмического декремента
        Показывает амплитуды пиков и их логарифмическое затухание
        """
        if self.processed_data is None or self.corrected_peaks is None or len(self.corrected_peaks) < 2:
            print("❌ Недостаточно данных для анализа логарифмического декремента")
            return
            
        try:
            time_processed = self.processed_data['Временная_метка']
            distance_processed = self.processed_data['Расстояние_норм']
            peaks = self.corrected_peaks
            
            # Получаем амплитуды и времена пиков
            peak_times = time_processed.iloc[peaks].values
            peak_amplitudes = distance_processed.iloc[peaks].values
            
            # Рассчитываем логарифм амплитуд
            log_amplitudes = np.log(np.abs(peak_amplitudes))
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # График 1: Амплитуды пиков
            ax1.plot(peak_times, peak_amplitudes, 'bo-', markersize=6, label='Амплитуды пиков')
            ax1.set_xlabel('Время (сек)')
            ax1.set_ylabel('Амплитуда (мм)')
            ax1.set_title('Зависимость амплитуд от времени')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # График 2: Логарифм амплитуд (должен быть линейным для экспоненциального затухания)
            ax2.plot(peak_times, log_amplitudes, 'ro-', markersize=6, label='ln(Амплитуда)')
            
            # Линейная аппроксимация
            if len(peak_times) >= 2:
                coeffs = np.polyfit(peak_times, log_amplitudes, 1)
                trend_line = np.polyval(coeffs, peak_times)
                ax2.plot(peak_times, trend_line, 'r--', alpha=0.7, 
                        label=f'Аппроксимация: y = {coeffs[0]:.4f}x + {coeffs[1]:.4f}')
                
                # Коэффициент затухания β = -slope
                beta = -coeffs[0]
                print(f"📉 Коэффициент затухания (β) из аппроксимации: {beta:.6f}")
            
            ax2.set_xlabel('Время (сек)')
            ax2.set_ylabel('ln(Амплитуда)')
            ax2.set_title('Логарифмическая зависимость амплитуд (должна быть линейной)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"❌ Ошибка построения графика логарифмического декремента: {e}")

    def save_results(self, period=None, frequency=None, input_filename=None):
        """Сохранение результатов анализа"""
        if self.processed_data is None:
            print("❌ Нет данных для сохранения")
            return False
            
        try:
            # Используем текущие значения если они есть
            save_period = self.current_period if self.current_period is not None else period
            save_frequency = self.current_frequency if self.current_frequency is not None else frequency
            
            # Сохраняем обработанные данные
            output_file = os.path.splitext(input_filename)[0] + "_processed.csv"
            self.processed_data.to_csv(output_file, sep=';', index=False, encoding='utf-8')
            print(f"💾 Обработанные данные сохранены в: {output_file}")
            
            # Сохраняем результаты анализа
            results_file = os.path.splitext(input_filename)[0] + "_analysis_results.txt"
            with open(results_file, 'w', encoding='utf-8') as f:
                f.write("РЕЗУЛЬТАТЫ АНАЛИЗА КОЛЕБАНИЙ РФ603\n")
                f.write("=" * 50 + "\n")
                f.write(f"Файл данных: {os.path.basename(input_filename)}\n")
                f.write(f"Дата анализа: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("ПАРАМЕТРЫ ОБРЕЗКИ:\n")
                f.write(f"Начальная точка: {self.oscillation_start}\n")
                f.write(f"Конечная точка: {self.oscillation_end}\n")
                f.write(f"Начальное время: {self.processed_data['Временная_метка'].iloc[0]:.6f} сек\n")
                f.write(f"Конечное время: {self.processed_data['Временная_метка'].iloc[-1]:.6f} сек\n")
                f.write(f"Всего точек: {len(self.processed_data)}\n\n")
                
                f.write("РЕЗУЛЬТАТЫ АНАЛИЗА:\n")
                if save_period is not None and save_frequency is not None:
                    f.write(f"Период колебаний: {save_period:.6f} сек\n")
                    f.write(f"Частота колебаний: {save_frequency:.2f} Гц\n")
                
                if self.log_decrement is not None:
                    f.write(f"Логарифмический декремент (δ): {self.log_decrement:.6f}\n")
                
                if self.damping_ratio is not None:
                    f.write(f"Коэффициент демпфирования (ζ): {self.damping_ratio:.6f}\n")
                
                if self.loss_factor is not None:
                    f.write(f"Коэффициент потерь (η): {self.loss_factor:.6f}\n")
                
                if self.corrected_peaks is not None:
                    f.write("Примечание: использованы исправленные пики\n")
            
            print(f"📄 Результаты анализа сохранены в: {results_file}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

def select_file():
    """Выбор файла через диалоговое окно"""
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.askopenfilename(
        title="Выберите CSV файл с данными РФ603",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    return file_path

def main():
    print("🎯 Анализатор колебаний РФ603 - УЛУЧШЕННАЯ версия с логарифмическим декрементом")
    print("=" * 50)
    
    analyzer = RF603OscillationAnalyzer()
    
    # Выбор файла
    input_file = select_file()
    if not input_file:
        print("❌ Файл не выбран")
        return
    
    # Загрузка данных
    if not analyzer.load_csv(input_file):
        return
    
    # Нормировка данных
    if not analyzer.normalize_data():
        return
    
    while True:
        print("\n" + "="*50)
        print("Выберите действие:")
        print("1. Показать необработанные данные")
        print("2. Обрезка по времени")
        print("3. Обрезка по точкам") 
        print("4. Автоматическая обрезка колебаний")
        print("5. Сбросить данные к исходным")
        print("6. Расчет периода и частоты")
        print("7. Ручная коррекция пиков")
        print("8. Детальный анализ периодов")
        print("9. Анализ логарифмического декремента")
        print("10. Сохранить результаты")
        print("11. Выход")
        
        choice = input("Ваш выбор (1-11): ").strip()
        
        if choice == '1':
            # Показать необработанные данные
            analyzer.plot_raw_data()
        
        elif choice == '2':
            # Обрезка по времени
            try:
                print(f"⏱️ Доступный временной диапазон: 0.0 - {analyzer.processed_data['Временная_метка'].iloc[-1]:.3f} сек")
                start_time = float(input("Время начала (сек): "))
                end_time = float(input("Время конца (сек): "))
                if analyzer.crop_by_time(start_time, end_time):
                    print("✅ Обрезка по времени выполнена")
                    # Показываем обновленный график
                    analyzer.plot_processed_data()
            except ValueError:
                print("❌ Неверный формат времени")
        
        elif choice == '3':
            # Обрезка по точкам
            try:
                print(f"📊 Всего точек: {len(analyzer.processed_data)}")
                start_point = int(input("Начальная точка: "))
                end_point = int(input("Конечная точка: "))
                if analyzer.crop_by_points(start_point, end_point):
                    print("✅ Обрезка по точкам выполнена")
                    # Показываем обновленный график
                    analyzer.plot_processed_data()
            except ValueError:
                print("❌ Неверный формат чисел")
        
        elif choice == '4':
            # Автоматическая обрезка
            try:
                duration = float(input("Длительность анализа после начала (сек) [1.0]: ") or "1.0")
            except ValueError:
                duration = 1.0
                
            success, period, frequency, peaks = analyzer.auto_crop_oscillations(duration_after_start=duration)
            if success:
                print("✅ Автоматическая обрезка выполнена")
                # Показываем обновленный график с результатами
                analyzer.plot_processed_data(period, frequency, peaks)
        
        elif choice == '5':
            # Сброс данных к исходным
            if analyzer.reset_to_original():
                print("✅ Данные сброшены к исходным")
                # Показываем обновленный график
                analyzer.plot_processed_data()
        
        elif choice == '6':
            # Расчет периода и частоты
            period, frequency, peaks = analyzer.calculate_period_frequency_improved()
            if period is not None:
                analyzer.plot_processed_data(period, frequency, peaks)
        
        elif choice == '7':
            # Ручная коррекция пиков
            period, frequency, peaks = analyzer.calculate_period_frequency_improved()
            if peaks is not None and len(peaks) > 0:
                try:
                    corrected_peaks = analyzer.manual_peak_correction(peaks)
                    # Пересчитываем с исправленными пиками
                    if len(corrected_peaks) >= 2:
                        timestamps = analyzer.processed_data['Временная_метка'].values
                        periods = []
                        for i in range(len(corrected_peaks) - 1):
                            period_val = timestamps[corrected_peaks[i + 1]] - timestamps[corrected_peaks[i]]
                            periods.append(period_val)
                        
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
                        
                        if filtered_periods:
                            avg_period = np.mean(filtered_periods)
                        else:
                            avg_period = np.mean(periods) if periods else 0
                        
                        frequency = 1.0 / avg_period if avg_period > 0 else 0
                        
                        # Сохраняем текущие значения
                        analyzer.current_period = avg_period
                        analyzer.current_frequency = frequency
                        
                        # Пересчитываем логарифмический декремент с исправленными пиками
                        analyzer.calculate_logarithmic_decrement(corrected_peaks)
                        
                        print(f"⏱️ Исправленный период: {avg_period:.6f} сек")
                        print(f"📊 Исправленная частота: {frequency:.2f} Гц")
                        
                        # Показываем график с исправленными пиками
                        analyzer.plot_processed_data(avg_period, frequency, corrected_peaks)
                    else:
                        print("❌ Недостаточно пиков для расчета периода (нужно минимум 2)")
                except Exception as e:
                    print(f"❌ Ошибка при ручной коррекции: {e}")
            else:
                print("❌ Нет пиков для коррекции")
        
        elif choice == '8':
            # Детальный анализ
            period, frequency, peaks = analyzer.calculate_period_frequency_improved()
            analyzer.plot_detailed_analysis(period, frequency, peaks)
        
        elif choice == '9':
            # Анализ логарифмического декремента
            if analyzer.corrected_peaks is not None and len(analyzer.corrected_peaks) >= 2:
                analyzer.plot_logarithmic_decrement_analysis()
            else:
                print("❌ Сначала выполните расчет периодов или ручную коррекцию пиков")
        
        elif choice == '10':
            # Сохранение результатов
            period, frequency, peaks = analyzer.calculate_period_frequency_improved()
            analyzer.save_results(period, frequency, input_file)
        
        elif choice == '11':
            break
        
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()