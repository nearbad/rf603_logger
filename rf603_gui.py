# -*- coding: utf-8 -*-
"""
RF603HS GUI - Главное приложение с графическим интерфейсом
Современный UI на базе PyQt5
"""

import sys
import os
import json
from datetime import datetime
from collections import deque
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QGroupBox, QSpinBox, QDoubleSpinBox, QLineEdit,
                             QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog,
                             QMessageBox, QProgressBar, QTabWidget, QCheckBox,
                             QSplitter, QAction, QMenuBar, QStatusBar, QDialog,
                             QFormLayout, QDialogButtonBox, QListWidget, QToolBar,
                             QRadioButton, QButtonGroup, QSlider, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Импортируем наши модули
from rf603_logger import RF603Sensor, DataRecorder, RF603OscillationAnalyzer


class ModernStyle:
    """Современные стили для приложения"""

    # Цветовая схема Material Design + научный стиль
    PRIMARY = "#2196F3"        # Синий
    PRIMARY_DARK = "#1976D2"   # Темно-синий
    ACCENT = "#FF5722"         # Оранжевый акцент
    SUCCESS = "#4CAF50"        # Зеленый
    WARNING = "#FFC107"        # Желтый
    ERROR = "#F44336"          # Красный
    BACKGROUND = "#FAFAFA"     # Светло-серый фон
    SURFACE = "#FFFFFF"        # Белый
    TEXT_PRIMARY = "#212121"   # Темный текст
    TEXT_SECONDARY = "#757575" # Серый текст

    @staticmethod
    def get_stylesheet():
        """Возвращает полный stylesheet для приложения"""
        return f"""
        QMainWindow {{
            background-color: {ModernStyle.BACKGROUND};
        }}

        QWidget {{
            font-family: 'Segoe UI', 'Roboto', 'Arial';
            font-size: 10pt;
        }}

        QGroupBox {{
            font-weight: bold;
            border: 2px solid {ModernStyle.PRIMARY};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: {ModernStyle.SURFACE};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: {ModernStyle.PRIMARY};
        }}

        QPushButton {{
            background-color: {ModernStyle.PRIMARY};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background-color: {ModernStyle.PRIMARY_DARK};
        }}

        QPushButton:pressed {{
            background-color: #0D47A1;
        }}

        QPushButton:disabled {{
            background-color: #BDBDBD;
            color: #757575;
        }}

        QPushButton.success {{
            background-color: {ModernStyle.SUCCESS};
        }}

        QPushButton.success:hover {{
            background-color: #388E3C;
        }}

        QPushButton.danger {{
            background-color: {ModernStyle.ERROR};
        }}

        QPushButton.danger:hover {{
            background-color: #D32F2F;
        }}

        QPushButton.warning {{
            background-color: {ModernStyle.WARNING};
            color: black;
        }}

        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
            border: 2px solid #E0E0E0;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
            min-height: 25px;
        }}

        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{
            border-color: {ModernStyle.PRIMARY};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 8px solid {ModernStyle.TEXT_SECONDARY};
            margin-right: 10px;
        }}

        QTextEdit, QTableWidget {{
            border: 2px solid #E0E0E0;
            border-radius: 4px;
            background-color: white;
        }}

        QTableWidget {{
            gridline-color: #E0E0E0;
        }}

        QTableWidget::item:selected {{
            background-color: {ModernStyle.PRIMARY};
            color: white;
        }}

        QHeaderView::section {{
            background-color: {ModernStyle.PRIMARY};
            color: white;
            padding: 5px;
            border: none;
            font-weight: bold;
        }}

        QTabWidget::pane {{
            border: 2px solid {ModernStyle.PRIMARY};
            border-radius: 4px;
            background-color: white;
        }}

        QTabBar::tab {{
            background-color: #E0E0E0;
            color: {ModernStyle.TEXT_PRIMARY};
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}

        QTabBar::tab:selected {{
            background-color: {ModernStyle.PRIMARY};
            color: white;
        }}

        QTabBar::tab:hover {{
            background-color: {ModernStyle.PRIMARY_DARK};
            color: white;
        }}

        QProgressBar {{
            border: 2px solid {ModernStyle.PRIMARY};
            border-radius: 4px;
            text-align: center;
            background-color: white;
        }}

        QProgressBar::chunk {{
            background-color: {ModernStyle.PRIMARY};
        }}

        QStatusBar {{
            background-color: {ModernStyle.SURFACE};
            border-top: 1px solid #E0E0E0;
        }}

        QMenuBar {{
            background-color: {ModernStyle.SURFACE};
            border-bottom: 1px solid #E0E0E0;
        }}

        QMenuBar::item:selected {{
            background-color: {ModernStyle.PRIMARY};
            color: white;
        }}

        QMenu::item:selected {{
            background-color: {ModernStyle.PRIMARY};
            color: white;
        }}

        QLabel.title {{
            font-size: 14pt;
            font-weight: bold;
            color: {ModernStyle.PRIMARY};
        }}

        QLabel.subtitle {{
            font-size: 11pt;
            font-weight: bold;
            color: {ModernStyle.TEXT_PRIMARY};
        }}

        QLabel.info {{
            color: {ModernStyle.TEXT_SECONDARY};
        }}

        QLabel.success {{
            color: {ModernStyle.SUCCESS};
            font-weight: bold;
        }}

        QLabel.error {{
            color: {ModernStyle.ERROR};
            font-weight: bold;
        }}

        QLabel.warning {{
            color: {ModernStyle.WARNING};
            font-weight: bold;
        }}
        """


class MplCanvas(FigureCanvas):
    """Canvas для matplotlib графиков"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

        # Настройка стиля графика
        self.axes.grid(True, alpha=0.3, linestyle='--')
        self.axes.set_facecolor('#FAFAFA')

    def clear_plot(self):
        """Очистка графика"""
        self.axes.clear()
        self.axes.grid(True, alpha=0.3, linestyle='--')
        self.axes.set_facecolor('#FAFAFA')


class DataRecordThread(QThread):
    """Поток для записи данных с датчика"""

    data_received = pyqtSignal(float, int, float)  # distance, point_num, time
    error_occurred = pyqtSignal(str)
    recording_stopped = pyqtSignal()

    def __init__(self, sensor):
        super().__init__()
        self.sensor = sensor
        self.is_recording = False
        self.start_time = None
        self.point_counter = 0
        self.data_points = []

    def run(self):
        """Основной цикл записи"""
        self.is_recording = True
        self.start_time = datetime.now()
        self.point_counter = 0

        # Запускаем поток данных
        self.sensor.start_data_stream()

        while self.is_recording:
            try:
                distance = self.sensor.read_stream_data()

                if distance is not None:
                    elapsed = (datetime.now() - self.start_time).total_seconds()

                    self.data_points.append({
                        'Расстояние_мм': distance,
                        'Номер_точки': self.point_counter,
                        'Временная_метка': elapsed
                    })

                    self.data_received.emit(distance, self.point_counter, elapsed)
                    self.point_counter += 1

                self.msleep(1)  # Небольшая задержка

            except Exception as e:
                self.error_occurred.emit(str(e))
                break

        # Останавливаем поток
        self.sensor.stop_data_stream()
        self.recording_stopped.emit()

    def stop(self):
        """Остановка записи"""
        self.is_recording = False
        self.wait()

    def get_data(self):
        """Получить записанные данные"""
        return self.data_points


class SettingsDialog(QDialog):
    """Диалог настроек"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.resize(500, 400)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout()

        # Вкладки настроек
        tabs = QTabWidget()

        # Вкладка "Общие"
        general_tab = QWidget()
        general_layout = QFormLayout()

        self.auto_save_check = QCheckBox("Автоматическое сохранение")
        self.auto_analyze_check = QCheckBox("Автоматический анализ после записи")
        self.show_notifications_check = QCheckBox("Показывать уведомления")

        general_layout.addRow("", self.auto_save_check)
        general_layout.addRow("", self.auto_analyze_check)
        general_layout.addRow("", self.show_notifications_check)

        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "Общие")

        # Вкладка "График"
        plot_tab = QWidget()
        plot_layout = QFormLayout()

        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(100, 100000)
        self.max_points_spin.setValue(10000)
        self.max_points_spin.setSuffix(" точек")

        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(10, 1000)
        self.update_interval_spin.setValue(100)
        self.update_interval_spin.setSuffix(" мс")

        plot_layout.addRow("Макс. точек на графике:", self.max_points_spin)
        plot_layout.addRow("Интервал обновления:", self.update_interval_spin)

        plot_tab.setLayout(plot_layout)
        tabs.addTab(plot_tab, "График")

        # Вкладка "Анализ"
        analysis_tab = QWidget()
        analysis_layout = QFormLayout()

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 10.0)
        self.threshold_spin.setValue(0.5)
        self.threshold_spin.setSuffix(" мм")
        self.threshold_spin.setDecimals(2)

        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 10.0)
        self.duration_spin.setValue(1.0)
        self.duration_spin.setSuffix(" сек")
        self.duration_spin.setDecimals(1)

        analysis_layout.addRow("Порог колебаний:", self.threshold_spin)
        analysis_layout.addRow("Длительность анализа:", self.duration_spin)

        analysis_tab.setLayout(analysis_layout)
        tabs.addTab(analysis_tab, "Анализ")

        layout.addWidget(tabs)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def load_settings(self):
        """Загрузка настроек"""
        settings = QSettings('RIFTEK', 'RF603Logger')

        self.auto_save_check.setChecked(settings.value('auto_save', True, type=bool))
        self.auto_analyze_check.setChecked(settings.value('auto_analyze', False, type=bool))
        self.show_notifications_check.setChecked(settings.value('show_notifications', True, type=bool))
        self.max_points_spin.setValue(settings.value('max_points', 10000, type=int))
        self.update_interval_spin.setValue(settings.value('update_interval', 100, type=int))
        self.threshold_spin.setValue(settings.value('threshold', 0.5, type=float))
        self.duration_spin.setValue(settings.value('duration', 1.0, type=float))

    def save_settings(self):
        """Сохранение настроек"""
        settings = QSettings('RIFTEK', 'RF603Logger')

        settings.setValue('auto_save', self.auto_save_check.isChecked())
        settings.setValue('auto_analyze', self.auto_analyze_check.isChecked())
        settings.setValue('show_notifications', self.show_notifications_check.isChecked())
        settings.setValue('max_points', self.max_points_spin.value())
        settings.setValue('update_interval', self.update_interval_spin.value())
        settings.setValue('threshold', self.threshold_spin.value())
        settings.setValue('duration', self.duration_spin.value())

    def accept(self):
        """Применить и закрыть"""
        self.save_settings()
        super().accept()


class ManualCropDialog(QDialog):
    """Диалог ручной обрезки данных"""

    def __init__(self, analyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.setWindowTitle("Ручная обрезка данных")
        self.setModal(True)
        self.resize(400, 300)

        self.init_ui()

    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout()

        # Информация о данных
        info_label = QLabel(f"<b>Всего точек данных:</b> {len(self.analyzer.processed_data)}")
        layout.addWidget(info_label)

        if len(self.analyzer.processed_data) > 0:
            time_range = self.analyzer.processed_data['Временная_метка'].iloc[-1]
            time_info = QLabel(f"<b>Временной диапазон:</b> 0.0 - {time_range:.3f} сек")
            layout.addWidget(time_info)

        # Вкладки для разных методов обрезки
        tabs = QTabWidget()

        # Вкладка "По времени"
        time_tab = QWidget()
        time_layout = QFormLayout()

        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 999999)
        self.start_time_spin.setDecimals(3)
        self.start_time_spin.setSuffix(" сек")

        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(0, 999999)
        self.end_time_spin.setDecimals(3)
        self.end_time_spin.setSuffix(" сек")

        if len(self.analyzer.processed_data) > 0:
            self.end_time_spin.setValue(self.analyzer.processed_data['Временная_метка'].iloc[-1])

        time_layout.addRow("Начало:", self.start_time_spin)
        time_layout.addRow("Конец:", self.end_time_spin)

        crop_time_btn = QPushButton("✂️ Обрезать по времени")
        crop_time_btn.clicked.connect(self.crop_by_time)
        time_layout.addRow("", crop_time_btn)

        time_tab.setLayout(time_layout)
        tabs.addTab(time_tab, "По времени")

        # Вкладка "По точкам"
        points_tab = QWidget()
        points_layout = QFormLayout()

        self.start_point_spin = QSpinBox()
        self.start_point_spin.setRange(0, len(self.analyzer.processed_data) - 1)

        self.end_point_spin = QSpinBox()
        self.end_point_spin.setRange(0, len(self.analyzer.processed_data) - 1)
        self.end_point_spin.setValue(len(self.analyzer.processed_data) - 1)

        points_layout.addRow("Начальная точка:", self.start_point_spin)
        points_layout.addRow("Конечная точка:", self.end_point_spin)

        crop_points_btn = QPushButton("✂️ Обрезать по точкам")
        crop_points_btn.clicked.connect(self.crop_by_points)
        points_layout.addRow("", crop_points_btn)

        points_tab.setLayout(points_layout)
        tabs.addTab(points_tab, "По точкам")

        layout.addWidget(tabs)

        # Кнопки
        buttons_layout = QHBoxLayout()

        reset_btn = QPushButton("🔄 Сбросить к исходным")
        reset_btn.clicked.connect(self.reset_data)
        buttons_layout.addWidget(reset_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def crop_by_time(self):
        """Обрезка по времени"""
        start_time = self.start_time_spin.value()
        end_time = self.end_time_spin.value()

        if start_time >= end_time:
            QMessageBox.warning(self, "Ошибка", "Начало должно быть меньше конца!")
            return

        if self.analyzer.crop_by_time(start_time, end_time):
            QMessageBox.information(self, "Успех",
                f"Данные обрезаны: {start_time:.3f} - {end_time:.3f} сек\n"
                f"Осталось точек: {len(self.analyzer.processed_data)}")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось обрезать данные!")

    def crop_by_points(self):
        """Обрезка по точкам"""
        start_point = self.start_point_spin.value()
        end_point = self.end_point_spin.value()

        if start_point >= end_point:
            QMessageBox.warning(self, "Ошибка", "Начальная точка должна быть меньше конечной!")
            return

        if self.analyzer.crop_by_points(start_point, end_point):
            QMessageBox.information(self, "Успех",
                f"Данные обрезаны: точки {start_point} - {end_point}\n"
                f"Осталось точек: {len(self.analyzer.processed_data)}")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось обрезать данные!")

    def reset_data(self):
        """Сброс к исходным данным"""
        reply = QMessageBox.question(self, "Подтверждение",
            "Вы уверены, что хотите сбросить все изменения?",
            QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.analyzer.reset_to_original():
                QMessageBox.information(self, "Успех", "Данные сброшены к исходным!")
                self.accept()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сбросить данные!")


class PeakCorrectionDialog(QDialog):
    """Диалог для ручной коррекции пиков"""

    def __init__(self, analyzer, peaks, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.original_peaks = peaks.copy() if peaks is not None else []
        self.corrected_peaks = peaks.copy() if peaks is not None else []

        self.setWindowTitle("Ручная коррекция пиков")
        self.setModal(True)
        self.resize(900, 600)

        self.init_ui()
        self.plot_peaks()

    def init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("<h3>Коррекция пиков колебаний</h3>")
        layout.addWidget(title)

        info = QLabel(
            "Используйте график для просмотра найденных пиков.\n"
            "Добавляйте/удаляйте пики в таблице ниже или вводите вручную."
        )
        layout.addWidget(info)

        # График
        self.canvas = MplCanvas(self, width=8, height=4, dpi=100)
        toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # Таблица пиков
        peaks_group = QGroupBox("Список пиков (номера точек)")
        peaks_layout = QVBoxLayout()

        self.peaks_table = QTableWidget()
        self.peaks_table.setColumnCount(3)
        self.peaks_table.setHorizontalHeaderLabels(['№', 'Индекс точки', 'Время (сек)'])
        self.peaks_table.setMaximumHeight(150)

        # Авто-размер столбцов
        header = self.peaks_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, header.Stretch)

        peaks_layout.addWidget(self.peaks_table)

        # Кнопки управления пиками
        peaks_buttons = QHBoxLayout()

        add_peak_btn = QPushButton("➕ Добавить пик")
        add_peak_btn.clicked.connect(self.add_peak)
        peaks_buttons.addWidget(add_peak_btn)

        remove_peak_btn = QPushButton("➖ Удалить выбранный")
        remove_peak_btn.clicked.connect(self.remove_peak)
        peaks_buttons.addWidget(remove_peak_btn)

        sort_btn = QPushButton("🔄 Сортировать")
        sort_btn.clicked.connect(self.sort_peaks)
        peaks_buttons.addWidget(sort_btn)

        peaks_layout.addLayout(peaks_buttons)
        peaks_group.setLayout(peaks_layout)
        layout.addWidget(peaks_group)

        # Кнопки OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Заполняем таблицу
        self.update_table()

    def plot_peaks(self):
        """Отображение графика с пиками"""
        self.canvas.clear_plot()

        data = self.analyzer.processed_data
        time_data = data['Временная_метка'].values
        distance_data = data['Расстояние_мм'].values

        # График данных
        self.canvas.axes.plot(time_data, distance_data, 'b-', linewidth=1.5, label='Данные')

        # Отмечаем пики
        if len(self.corrected_peaks) > 0:
            peak_times = time_data[self.corrected_peaks]
            peak_values = distance_data[self.corrected_peaks]
            self.canvas.axes.plot(peak_times, peak_values, 'ro', markersize=8, label=f'Пики ({len(self.corrected_peaks)})')

            # Нумеруем пики
            for i, (t, v) in enumerate(zip(peak_times, peak_values)):
                self.canvas.axes.annotate(f'{i+1}', (t, v),
                    textcoords="offset points", xytext=(0,10), ha='center',
                    fontsize=8, color='red', fontweight='bold')

        self.canvas.axes.set_xlabel('Время (сек)', fontsize=10)
        self.canvas.axes.set_ylabel('Расстояние (мм)', fontsize=10)
        self.canvas.axes.set_title(f'Коррекция пиков (всего: {len(self.corrected_peaks)})', fontsize=12, fontweight='bold')
        self.canvas.axes.legend()
        self.canvas.axes.grid(True, alpha=0.3, linestyle='--')
        self.canvas.draw()

    def update_table(self):
        """Обновление таблицы пиков"""
        self.peaks_table.setRowCount(len(self.corrected_peaks))

        data = self.analyzer.processed_data
        time_data = data['Временная_метка'].values

        for i, peak_idx in enumerate(self.corrected_peaks):
            self.peaks_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.peaks_table.setItem(i, 1, QTableWidgetItem(str(peak_idx)))
            self.peaks_table.setItem(i, 2, QTableWidgetItem(f"{time_data[peak_idx]:.3f}"))

    def add_peak(self):
        """Добавление пика"""
        peak_idx, ok = QInputDialog.getInt(self, "Добавить пик",
            f"Введите номер точки (0-{len(self.analyzer.processed_data)-1}):",
            0, 0, len(self.analyzer.processed_data)-1)

        if ok:
            if peak_idx not in self.corrected_peaks:
                self.corrected_peaks.append(peak_idx)
                self.sort_peaks()
                self.update_table()
                self.plot_peaks()
            else:
                QMessageBox.warning(self, "Предупреждение", "Этот пик уже есть в списке!")

    def remove_peak(self):
        """Удаление выбранного пика"""
        current_row = self.peaks_table.currentRow()
        if current_row >= 0:
            del self.corrected_peaks[current_row]
            self.update_table()
            self.plot_peaks()
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите пик для удаления!")

    def sort_peaks(self):
        """Сортировка пиков"""
        self.corrected_peaks.sort()
        self.update_table()
        self.plot_peaks()

    def get_corrected_peaks(self):
        """Получить откорректированные пики"""
        return self.corrected_peaks


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()

        # Инициализация данных
        self.sensor = RF603Sensor()
        self.record_thread = None
        self.is_recording = False
        self.current_file = None
        self.analyzer = None  # Для хранения анализатора данных

        # Данные для графика
        self.time_data = deque(maxlen=10000)
        self.distance_data = deque(maxlen=10000)

        # Настройки
        self.settings = QSettings('RIFTEK', 'RF603Logger')

        # Инициализация UI
        self.init_ui()

        # Таймер для обновления списка портов
        self.port_update_timer = QTimer()
        self.port_update_timer.timeout.connect(self.update_port_list)
        self.port_update_timer.start(3000)  # Каждые 3 секунды

        # Начальное обновление портов
        self.update_port_list()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("RF603HS Logger & Analyzer - Профессиональная система")
        self.setGeometry(100, 100, 1280, 720)

        # Применяем стили
        self.setStyleSheet(ModernStyle.get_stylesheet())

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный layout
        main_layout = QHBoxLayout()

        # Левая часть - График (60%)
        left_widget = self.create_plot_widget()

        # Правая часть - Панель управления (40%)
        right_widget = self.create_control_panel()

        # Splitter для изменения размеров
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # Создаем меню
        self.create_menu()

        # Создаем статус бар
        self.create_status_bar()

    def create_plot_widget(self):
        """Создание виджета с графиком"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("График в реальном времени")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Canvas для графика
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        self.canvas.axes.set_xlabel('Время (сек)', fontsize=10)
        self.canvas.axes.set_ylabel('Расстояние (мм)', fontsize=10)
        self.canvas.axes.set_title('Ожидание данных...', fontsize=12, fontweight='bold')

        # Toolbar для графика
        toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        widget.setLayout(layout)
        return widget

    def create_control_panel(self):
        """Создание панели управления"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Вкладки
        tabs = QTabWidget()

        # Вкладка "Подключение"
        connection_tab = self.create_connection_tab()
        tabs.addTab(connection_tab, "🔌 Подключение")

        # Вкладка "Запись"
        recording_tab = self.create_recording_tab()
        tabs.addTab(recording_tab, "🔴 Запись")

        # Вкладка "Статистика"
        stats_tab = self.create_stats_tab()
        tabs.addTab(stats_tab, "📊 Статистика")

        # Вкладка "Данные"
        data_tab = self.create_data_tab()
        tabs.addTab(data_tab, "📋 Данные")

        # Вкладка "Лог"
        log_tab = self.create_log_tab()
        tabs.addTab(log_tab, "📝 Лог")

        layout.addWidget(tabs)
        widget.setLayout(layout)
        return widget

    def create_connection_tab(self):
        """Вкладка подключения"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Группа "Выбор порта"
        port_group = QGroupBox("Выбор COM-порта")
        port_layout = QVBoxLayout()

        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(35)
        port_layout.addWidget(QLabel("COM-порт:"))
        port_layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self.update_port_list)
        port_layout.addWidget(refresh_btn)

        port_group.setLayout(port_layout)
        layout.addWidget(port_group)

        # Группа "Настройки"
        settings_group = QGroupBox("Настройки подключения")
        settings_layout = QFormLayout()

        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['9600', '19200', '57600', '115200', '460800'])
        self.baudrate_combo.setCurrentText('9600')
        self.baudrate_combo.setMinimumHeight(35)

        self.address_spin = QSpinBox()
        self.address_spin.setRange(1, 127)
        self.address_spin.setValue(1)
        self.address_spin.setMinimumHeight(30)

        settings_layout.addRow("Baud Rate:", self.baudrate_combo)
        settings_layout.addRow("Адрес датчика:", self.address_spin)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Кнопка подключения
        self.connect_btn = QPushButton("🔌 Подключиться")
        self.connect_btn.setMinimumHeight(45)
        self.connect_btn.setProperty("class", "success")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)

        # Информация о датчике
        info_group = QGroupBox("Информация о датчике")
        info_layout = QFormLayout()

        self.info_type = QLabel("-")
        self.info_serial = QLabel("-")
        self.info_base = QLabel("-")
        self.info_range = QLabel("-")

        info_layout.addRow("Тип:", self.info_type)
        info_layout.addRow("Серийный №:", self.info_serial)
        info_layout.addRow("Базовое расст.:", self.info_base)
        info_layout.addRow("Диапазон:", self.info_range)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_recording_tab(self):
        """Вкладка записи"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Кнопки управления
        self.start_btn = QPushButton("▶️ Начать запись")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setEnabled(False)
        self.start_btn.setProperty("class", "success")
        self.start_btn.clicked.connect(self.start_recording)

        self.stop_btn = QPushButton("⏹ Остановить запись")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.clicked.connect(self.stop_recording)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        # Прогресс
        progress_group = QGroupBox("Прогресс записи")
        progress_layout = QVBoxLayout()

        self.points_label = QLabel("Точек записано: 0")
        self.time_label = QLabel("Время записи: 0.00 сек")
        self.rate_label = QLabel("Скорость: 0 точек/сек")

        progress_layout.addWidget(self.points_label)
        progress_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.rate_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Настройки записи
        settings_group = QGroupBox("Настройки записи")
        settings_layout = QFormLayout()

        self.auto_save_check = QCheckBox()
        self.auto_save_check.setChecked(True)

        self.filename_edit = QLineEdit()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename_edit.setText(f"rf603_data_{timestamp}.csv")

        settings_layout.addRow("Автосохранение:", self.auto_save_check)
        settings_layout.addRow("Имя файла:", self.filename_edit)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_stats_tab(self):
        """Вкладка статистики"""
        widget = QWidget()
        layout = QVBoxLayout()

        stats_group = QGroupBox("Статистика измерений")
        stats_layout = QFormLayout()

        self.stat_current = QLabel("-")
        self.stat_min = QLabel("-")
        self.stat_max = QLabel("-")
        self.stat_avg = QLabel("-")
        self.stat_std = QLabel("-")

        stats_layout.addRow("Текущее:", self.stat_current)
        stats_layout.addRow("Минимум:", self.stat_min)
        stats_layout.addRow("Максимум:", self.stat_max)
        stats_layout.addRow("Среднее:", self.stat_avg)
        stats_layout.addRow("Ст. откл.:", self.stat_std)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Кнопки анализа
        analysis_group = QGroupBox("Анализ данных")
        analysis_layout = QVBoxLayout()

        self.analyze_btn = QPushButton("🔬 Анализировать текущие данные")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self.analyze_data)

        self.open_file_btn = QPushButton("📂 Открыть файл для анализа")
        self.open_file_btn.clicked.connect(self.open_file_for_analysis)

        # Кнопки ручной обработки
        self.manual_crop_btn = QPushButton("✂️ Ручная обрезка данных")
        self.manual_crop_btn.setEnabled(False)
        self.manual_crop_btn.clicked.connect(self.manual_crop_data)

        self.manual_peaks_btn = QPushButton("📍 Ручная коррекция пиков")
        self.manual_peaks_btn.setEnabled(False)
        self.manual_peaks_btn.clicked.connect(self.manual_correct_peaks)

        analysis_layout.addWidget(self.analyze_btn)
        analysis_layout.addWidget(self.open_file_btn)
        analysis_layout.addWidget(self.manual_crop_btn)
        analysis_layout.addWidget(self.manual_peaks_btn)

        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        # Результаты анализа
        results_group = QGroupBox("Результаты анализа")
        results_layout = QFormLayout()

        self.result_period = QLabel("-")
        self.result_freq = QLabel("-")
        self.result_decrement = QLabel("-")
        self.result_damping = QLabel("-")
        self.result_loss = QLabel("-")

        results_layout.addRow("Период:", self.result_period)
        results_layout.addRow("Частота:", self.result_freq)
        results_layout.addRow("Лог. декремент:", self.result_decrement)
        results_layout.addRow("Демпфирование:", self.result_damping)
        results_layout.addRow("Коэф. потерь:", self.result_loss)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_data_tab(self):
        """Вкладка данных"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Таблица данных
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(['Расст. (мм)', '№ точки', 'Время (сек)'])
        self.data_table.setMaximumHeight(250)

        # Устанавливаем ширину столбцов
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, header.Stretch)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, header.Stretch)

        layout.addWidget(QLabel("Последние измерения:"))
        layout.addWidget(self.data_table)

        # Кнопки управления данными
        buttons_layout = QHBoxLayout()

        clear_btn = QPushButton("🗑️ Очистить")
        clear_btn.clicked.connect(self.clear_data)

        export_btn = QPushButton("💾 Экспорт")
        export_btn.clicked.connect(self.export_data)

        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(export_btn)

        layout.addLayout(buttons_layout)

        widget.setLayout(layout)
        return widget

    def create_log_tab(self):
        """Вкладка лога"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(400)

        layout.addWidget(QLabel("Лог событий:"))
        layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("🗑️ Очистить лог")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(clear_log_btn)

        widget.setLayout(layout)
        return widget

    def create_menu(self):
        """Создание меню"""
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu("&Файл")

        open_action = QAction("📂 Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file_for_analysis)
        file_menu.addAction(open_action)

        save_action = QAction("💾 Сохранить...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_current_data)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Инструменты"
        tools_menu = menubar.addMenu("&Инструменты")

        settings_action = QAction("⚙️ Настройки...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # Меню "Помощь"
        help_menu = menubar.addMenu("&Помощь")

        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        """Создание статус бара"""
        self.statusBar().showMessage("Готов к работе")

    def log(self, message, level="INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": "black",
            "SUCCESS": "green",
            "WARNING": "orange",
            "ERROR": "red"
        }.get(level, "black")

        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        self.log_text.append(formatted_message)

    def update_port_list(self):
        """Обновление списка портов"""
        import serial.tools.list_ports

        current_port = self.port_combo.currentText()
        self.port_combo.clear()

        ports = list(serial.tools.list_ports.comports())
        if ports:
            for port in ports:
                self.port_combo.addItem(f"{port.device} - {port.description}")

            # Восстанавливаем выбранный порт если он еще доступен
            index = self.port_combo.findText(current_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        else:
            self.port_combo.addItem("Нет доступных портов")

    def toggle_connection(self):
        """Переключение подключения"""
        if not self.sensor.is_connected:
            self.connect_sensor()
        else:
            self.disconnect_sensor()

    def connect_sensor(self):
        """Подключение к датчику"""
        port_text = self.port_combo.currentText()
        if "Нет доступных" in port_text:
            QMessageBox.warning(self, "Ошибка", "Нет доступных COM-портов!")
            return

        port = port_text.split(" - ")[0]
        baudrate = int(self.baudrate_combo.currentText())
        address = self.address_spin.value()

        self.log(f"Попытка подключения к {port} на скорости {baudrate}...")

        if self.sensor.connect(port, baudrate, address):
            self.log("✅ Подключение успешно!", "SUCCESS")

            # Обновляем UI
            self.connect_btn.setText("🔌 Отключиться")
            self.connect_btn.setProperty("class", "danger")
            self.connect_btn.style().unpolish(self.connect_btn)
            self.connect_btn.style().polish(self.connect_btn)

            self.start_btn.setEnabled(True)

            # Обновляем информацию о датчике
            info = self.sensor.device_info
            self.info_type.setText(str(info.get('type', '-')))
            self.info_serial.setText(str(info.get('serial', '-')))
            self.info_base.setText(f"{info.get('base_distance', '-')} мм")
            self.info_range.setText(f"{info.get('range', '-')} мм")

            self.statusBar().showMessage(f"Подключено к {port}")

        else:
            self.log("❌ Не удалось подключиться", "ERROR")
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к датчику!")

    def disconnect_sensor(self):
        """Отключение от датчика"""
        self.sensor.disconnect()
        self.log("Отключено от датчика", "INFO")

        # Обновляем UI
        self.connect_btn.setText("🔌 Подключиться")
        self.connect_btn.setProperty("class", "success")
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)

        self.start_btn.setEnabled(False)

        # Очищаем информацию
        self.info_type.setText("-")
        self.info_serial.setText("-")
        self.info_base.setText("-")
        self.info_range.setText("-")

        self.statusBar().showMessage("Отключено")

    def start_recording(self):
        """Начало записи"""
        if not self.sensor.is_connected:
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к датчику!")
            return

        # Очищаем данные
        self.time_data.clear()
        self.distance_data.clear()
        self.canvas.clear_plot()
        self.canvas.axes.set_title('Запись данных...', fontsize=12, fontweight='bold', color='red')
        self.canvas.draw()

        # Создаем и запускаем поток записи
        self.record_thread = DataRecordThread(self.sensor)
        self.record_thread.data_received.connect(self.on_data_received)
        self.record_thread.error_occurred.connect(self.on_record_error)
        self.record_thread.recording_stopped.connect(self.on_recording_stopped)
        self.record_thread.start()

        self.is_recording = True

        # Обновляем UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.connect_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)

        self.log("🔴 Запись начата", "SUCCESS")
        self.statusBar().showMessage("⏺ Идет запись...")

    def stop_recording(self):
        """Остановка записи"""
        if self.record_thread:
            self.log("⏹ Остановка записи...", "INFO")
            self.record_thread.stop()

    def on_data_received(self, distance, point_num, elapsed_time):
        """Обработка полученных данных"""
        # Добавляем в буфер
        self.time_data.append(elapsed_time)
        self.distance_data.append(distance)

        # Обновляем график (каждые 10 точек для производительности)
        if point_num % 10 == 0:
            self.update_plot()

        # Обновляем статистику
        self.update_statistics()

        # Обновляем прогресс
        self.points_label.setText(f"Точек записано: {point_num}")
        self.time_label.setText(f"Время записи: {elapsed_time:.2f} сек")
        if elapsed_time > 0:
            rate = point_num / elapsed_time
            self.rate_label.setText(f"Скорость: {rate:.0f} точек/сек")

        # Обновляем таблицу (только последние 20 строк)
        if self.data_table.rowCount() < 20:
            row = self.data_table.rowCount()
            self.data_table.insertRow(row)
            self.data_table.setItem(row, 0, QTableWidgetItem(f"{distance:.3f}"))
            self.data_table.setItem(row, 1, QTableWidgetItem(str(point_num)))
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{elapsed_time:.3f}"))

    def on_record_error(self, error_msg):
        """Обработка ошибки записи"""
        self.log(f"❌ Ошибка: {error_msg}", "ERROR")
        QMessageBox.critical(self, "Ошибка записи", f"Произошла ошибка:\n{error_msg}")

    def on_recording_stopped(self):
        """Обработка остановки записи"""
        self.is_recording = False

        # Обновляем UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.connect_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)

        self.canvas.axes.set_title('Запись завершена', fontsize=12, fontweight='bold', color='green')
        self.canvas.draw()

        self.log("✅ Запись остановлена", "SUCCESS")
        self.statusBar().showMessage("Готов к работе")

        # Автосохранение
        if self.auto_save_check.isChecked():
            self.save_current_data()

    def update_plot(self):
        """Обновление графика"""
        if len(self.time_data) > 0:
            self.canvas.axes.clear()
            self.canvas.axes.plot(list(self.time_data), list(self.distance_data),
                                 'b-', linewidth=1.5, label='Расстояние')
            self.canvas.axes.set_xlabel('Время (сек)', fontsize=10)
            self.canvas.axes.set_ylabel('Расстояние (мм)', fontsize=10)
            self.canvas.axes.set_title('Данные с датчика RF603HS', fontsize=12, fontweight='bold')
            self.canvas.axes.grid(True, alpha=0.3, linestyle='--')
            self.canvas.axes.legend()
            self.canvas.draw()

    def update_statistics(self):
        """Обновление статистики"""
        if len(self.distance_data) > 0:
            data = np.array(list(self.distance_data))

            self.stat_current.setText(f"{data[-1]:.3f} мм")
            self.stat_min.setText(f"{np.min(data):.3f} мм")
            self.stat_max.setText(f"{np.max(data):.3f} мм")
            self.stat_avg.setText(f"{np.mean(data):.3f} мм")
            self.stat_std.setText(f"{np.std(data):.3f} мм")

    def save_current_data(self):
        """Сохранение текущих данных"""
        if not self.record_thread or not self.record_thread.data_points:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для сохранения!")
            return

        filename = self.filename_edit.text()
        if not filename.endswith('.csv'):
            filename += '.csv'

        try:
            df = pd.DataFrame(self.record_thread.data_points)
            df.to_csv(filename, sep=';', index=False, encoding='utf-8')

            self.current_file = filename
            self.log(f"💾 Данные сохранены: {filename}", "SUCCESS")
            QMessageBox.information(self, "Успех", f"Данные сохранены в файл:\n{filename}")

        except Exception as e:
            self.log(f"❌ Ошибка сохранения: {e}", "ERROR")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")

    def clear_data(self):
        """Очистка данных"""
        reply = QMessageBox.question(self, "Подтверждение",
                                    "Вы уверены, что хотите очистить все данные?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.time_data.clear()
            self.distance_data.clear()
            self.data_table.setRowCount(0)
            self.canvas.clear_plot()
            self.canvas.axes.set_title('Ожидание данных...', fontsize=12)
            self.canvas.draw()

            self.log("🗑️ Данные очищены", "INFO")

    def export_data(self):
        """Экспорт данных"""
        if not self.record_thread or not self.record_thread.data_points:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для экспорта!")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Экспорт данных", "",
                                                 "CSV файлы (*.csv);;Excel файлы (*.xlsx);;Все файлы (*)")

        if filename:
            try:
                df = pd.DataFrame(self.record_thread.data_points)

                if filename.endswith('.xlsx'):
                    df.to_excel(filename, index=False)
                else:
                    df.to_csv(filename, sep=';', index=False, encoding='utf-8')

                self.log(f"💾 Экспорт выполнен: {filename}", "SUCCESS")
                QMessageBox.information(self, "Успех", f"Данные экспортированы в:\n{filename}")

            except Exception as e:
                self.log(f"❌ Ошибка экспорта: {e}", "ERROR")
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать:\n{e}")

    def analyze_data(self):
        """Анализ данных"""
        if self.current_file:
            self.perform_analysis(self.current_file)
        elif self.record_thread and self.record_thread.data_points:
            # Сохраняем временный файл
            temp_file = "temp_analysis.csv"
            df = pd.DataFrame(self.record_thread.data_points)
            df.to_csv(temp_file, sep=';', index=False, encoding='utf-8')
            self.perform_analysis(temp_file)
        else:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для анализа!")

    def open_file_for_analysis(self):
        """Открытие файла для анализа"""
        filename, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "CSV файлы (*.csv);;Все файлы (*)")

        if filename:
            self.perform_analysis(filename)

    def perform_analysis(self, filename):
        """Выполнение анализа"""
        try:
            self.log(f"🔬 Начало анализа файла: {filename}", "INFO")

            # Создаем новый анализатор
            self.analyzer = RF603OscillationAnalyzer()

            if not self.analyzer.load_csv(filename):
                raise Exception("Не удалось загрузить файл")

            # Всегда показываем загруженные данные на графике
            self.log(f"📊 Загружено {len(self.analyzer.data)} точек данных", "INFO")

            # Включаем кнопки ручной обработки
            self.manual_crop_btn.setEnabled(True)
            self.manual_peaks_btn.setEnabled(True)

            # Отображаем данные на графике GUI
            self.update_analysis_plot()

            if not self.analyzer.normalize_data():
                raise Exception("Ошибка нормировки данных")

            # Параметры из настроек
            settings = QSettings('RIFTEK', 'RF603Logger')
            duration = settings.value('duration', 1.0, type=float)

            success, period, freq, peaks = self.analyzer.auto_crop_oscillations(duration)

            # Обновляем результаты, если они есть
            if period is not None:
                self.result_period.setText(f"{period:.6f} сек")
            else:
                self.result_period.setText("-")

            if freq is not None:
                self.result_freq.setText(f"{freq:.2f} Гц")
            else:
                self.result_freq.setText("-")

            if self.analyzer.log_decrement is not None:
                self.result_decrement.setText(f"{self.analyzer.log_decrement:.6f}")
                self.result_damping.setText(f"{self.analyzer.damping_ratio:.6f}")
                self.result_loss.setText(f"{self.analyzer.loss_factor:.6f}")
            else:
                self.result_decrement.setText("-")
                self.result_damping.setText("-")
                self.result_loss.setText("-")

            if success:
                self.log("✅ Анализ завершен успешно!", "SUCCESS")
                # Обновляем график с результатами
                self.update_analysis_plot()
                # Показываем результаты в отдельном окне
                self.analyzer.plot_results()
            else:
                # Частичный успех - данные загружены, но автоанализ не удался
                self.log("⚠️ Автоматический анализ не удался (недостаточно пиков)", "WARNING")
                self.log("💡 Используйте кнопки ручной обработки ниже", "INFO")

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Частичный результат")
                msg.setText("Данные загружены и отображены на графике.")
                msg.setInformativeText(
                    "Автоматический анализ не удался (недостаточно пиков для расчета).\n\n"
                    "Рекомендации:\n"
                    "1. Проверьте данные на графике\n"
                    "2. Используйте dekrement.py для ручной обработки\n"
                    "3. Попробуйте изменить параметры анализа в настройках"
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        except Exception as e:
            self.log(f"❌ Ошибка анализа: {e}", "ERROR")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при анализе:\n{e}")

    def update_analysis_plot(self):
        """Обновление графика с данными из analyzer"""
        if self.analyzer and hasattr(self.analyzer, 'processed_data') and len(self.analyzer.processed_data) > 0:
            time_data = self.analyzer.processed_data['Временная_метка'].values
            distance_data = self.analyzer.processed_data['Расстояние_мм'].values

            self.canvas.clear_plot()
            self.canvas.axes.plot(time_data, distance_data, 'b-', linewidth=1.5, label='Данные')
            self.canvas.axes.set_xlabel('Время (сек)', fontsize=10)
            self.canvas.axes.set_ylabel('Расстояние (мм)', fontsize=10)
            self.canvas.axes.set_title('Данные для анализа', fontsize=12, fontweight='bold')
            self.canvas.axes.legend()
            self.canvas.axes.grid(True, alpha=0.3, linestyle='--')
            self.canvas.draw()

    def manual_crop_data(self):
        """Открыть диалог ручной обрезки данных"""
        if not self.analyzer:
            QMessageBox.warning(self, "Предупреждение",
                "Сначала откройте файл для анализа!")
            return

        dialog = ManualCropDialog(self.analyzer, self)
        if dialog.exec_() == QDialog.Accepted:
            # Данные обновлены, обновляем график
            self.update_analysis_plot()
            self.log("✅ Данные обрезаны вручную", "SUCCESS")

            # Пробуем снова выполнить автоанализ с новыми данными
            try:
                period, frequency, peaks = self.analyzer.calculate_period_frequency_improved()
                if period is not None:
                    self.result_period.setText(f"{period:.6f} сек")
                    self.result_freq.setText(f"{frequency:.2f} Гц")

                    if peaks is not None and len(peaks) >= 2:
                        # Вычисляем логарифмический декремент
                        self.analyzer.calculate_logarithmic_decrement(peaks)
                        if self.analyzer.log_decrement:
                            self.result_decrement.setText(f"{self.analyzer.log_decrement:.6f}")
                            self.result_damping.setText(f"{self.analyzer.damping_ratio:.6f}")
                            self.result_loss.setText(f"{self.analyzer.loss_factor:.6f}")

                    self.log("✅ Повторный анализ завершен", "SUCCESS")
            except Exception as e:
                self.log(f"⚠️ Повторный анализ: {e}", "WARNING")

    def manual_correct_peaks(self):
        """Открыть диалог ручной коррекции пиков"""
        if not self.analyzer:
            QMessageBox.warning(self, "Предупреждение",
                "Сначала откройте файл для анализа!")
            return

        # Сначала находим пики автоматически
        try:
            period, frequency, peaks = self.analyzer.calculate_period_frequency_improved()

            if peaks is None or len(peaks) == 0:
                # Нет автоматических пиков, предлагаем создать вручную
                reply = QMessageBox.question(self, "Пики не найдены",
                    "Автоматически пики не найдены. Хотите создать пики вручную?",
                    QMessageBox.Yes | QMessageBox.No)

                if reply == QMessageBox.Yes:
                    peaks = []  # Пустой список для ручного заполнения
                else:
                    return
        except Exception as e:
            self.log(f"❌ Ошибка поиска пиков: {e}", "ERROR")
            return

        # Открываем диалог коррекции
        dialog = PeakCorrectionDialog(self.analyzer, peaks, self)
        if dialog.exec_() == QDialog.Accepted:
            corrected_peaks = dialog.get_corrected_peaks()

            if len(corrected_peaks) >= 2:
                self.log(f"✅ Пики откорректированы: {len(corrected_peaks)} пиков", "SUCCESS")

                # Пересчитываем с исправленными пиками
                timestamps = self.analyzer.processed_data['Временная_метка'].values
                periods = []
                for i in range(len(corrected_peaks) - 1):
                    period_val = timestamps[corrected_peaks[i + 1]] - timestamps[corrected_peaks[i]]
                    periods.append(period_val)

                if periods:
                    avg_period = np.mean(periods)
                    avg_frequency = 1.0 / avg_period if avg_period > 0 else 0

                    self.result_period.setText(f"{avg_period:.6f} сек")
                    self.result_freq.setText(f"{avg_frequency:.2f} Гц")

                    # Вычисляем логарифмический декремент
                    self.analyzer.calculate_logarithmic_decrement(corrected_peaks)
                    if self.analyzer.log_decrement:
                        self.result_decrement.setText(f"{self.analyzer.log_decrement:.6f}")
                        self.result_damping.setText(f"{self.analyzer.damping_ratio:.6f}")
                        self.result_loss.setText(f"{self.analyzer.loss_factor:.6f}")

                    self.log("✅ Анализ с ручными пиками завершен", "SUCCESS")

                    # Обновляем график
                    self.update_analysis_plot()
            else:
                QMessageBox.warning(self, "Предупреждение",
                    "Недостаточно пиков для анализа (минимум 2)!")

    def show_settings(self):
        """Показ диалога настроек"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.log("⚙️ Настройки сохранены", "SUCCESS")

    def show_about(self):
        """Показ информации о программе"""
        about_text = """
        <h2>RF603HS Logger & Analyzer</h2>
        <p><b>Версия:</b> 2.0 (GUI Edition)</p>
        <p><b>Дата:</b> 2025-10-27</p>
        <p>Профессиональная система для работы с лазерным<br>
        триангуляционным датчиком RIFTEK RF603HS</p>
        <hr>
        <p><b>Возможности:</b></p>
        <ul>
            <li>Подключение к датчику через COM-порт</li>
            <li>Запись данных в реальном времени</li>
            <li>Визуализация с обновлением графика</li>
            <li>Автоматический анализ затухающих колебаний</li>
            <li>Расчет физических параметров</li>
            <li>Экспорт данных и отчетов</li>
        </ul>
        <hr>
        <p><b>Разработано с помощью Claude Code</b></p>
        <p>© 2025 RIFTEK</p>
        """

        QMessageBox.about(self, "О программе", about_text)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.is_recording:
            reply = QMessageBox.question(self, "Подтверждение",
                                        "Идет запись данных. Вы уверены, что хотите выйти?",
                                        QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.No:
                event.ignore()
                return

            # Останавливаем запись
            if self.record_thread:
                self.record_thread.stop()

        # Отключаемся от датчика
        if self.sensor.is_connected:
            self.sensor.disconnect()

        event.accept()


def main():
    """Главная функция"""
    app = QApplication(sys.argv)

    # Устанавливаем иконку приложения (если есть)
    # app.setWindowIcon(QIcon('icon.png'))

    # Устанавливаем название приложения
    app.setApplicationName("RF603HS Logger")
    app.setOrganizationName("RIFTEK")

    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
