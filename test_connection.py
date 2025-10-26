# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки подключения к датчику RF603HS
"""

import serial
import serial.tools.list_ports
import time
import sys

def test_port(port, baudrate):
    """Тест подключения к порту"""
    try:
        print(f"\n{'='*60}")
        print(f"Тест порта: {port} на скорости {baudrate} бод")
        print('='*60)

        # Открываем порт
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=2
        )

        print("✅ Порт открыт успешно")
        time.sleep(0.5)

        # Очищаем буферы
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("✅ Буферы очищены")

        # Отправляем запрос идентификации
        request = bytes([0x01, 0x81])  # Адрес 1, запрос 01h
        print(f"📤 Отправка запроса: {request.hex()}")
        ser.write(request)

        time.sleep(0.2)

        # Читаем ответ
        response = ser.read(16)
        print(f"📥 Получен ответ ({len(response)} байт): {response.hex()}")

        if len(response) >= 16:
            # Декодируем базовое расстояние
            base_low = (response[8] & 0x0F) | ((response[9] & 0x0F) << 4)
            base_high = (response[10] & 0x0F) | ((response[11] & 0x0F) << 4)
            base_distance = (base_high << 8) | base_low

            # Декодируем диапазон
            range_low = (response[12] & 0x0F) | ((response[13] & 0x0F) << 4)
            range_high = (response[14] & 0x0F) | ((response[15] & 0x0F) << 4)
            measurement_range = (range_high << 8) | range_low

            print("\n" + "="*60)
            print("ИНФОРМАЦИЯ О ДАТЧИКЕ:")
            print("="*60)
            print(f"Базовое расстояние: {base_distance} мм")
            print(f"Диапазон измерения: {measurement_range} мм")
            print("="*60)

            # Тест чтения одного измерения
            print("\nТест чтения измерения...")
            request_measure = bytes([0x01, 0x86])  # Запрос 06h
            ser.write(request_measure)

            time.sleep(0.1)

            measure_response = ser.read(4)
            print(f"📥 Ответ измерения ({len(measure_response)} байт): {measure_response.hex()}")

            if len(measure_response) >= 4:
                # Декодируем результат
                low_byte = (measure_response[0] & 0x0F) | ((measure_response[1] & 0x0F) << 4)
                high_byte = (measure_response[2] & 0x0F) | ((measure_response[3] & 0x0F) << 4)
                raw_value = (high_byte << 8) | low_byte

                distance_mm = (raw_value * measurement_range) / 0x4000
                print(f"📏 Измеренное расстояние: {distance_mm:.3f} мм")

                print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
                ser.close()
                return True

        print("\n❌ Датчик не ответил корректно")
        ser.close()
        return False

    except serial.SerialException as e:
        print(f"\n❌ Ошибка работы с портом: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return False


def main():
    """Главная функция"""
    print("="*70)
    print(" "*15 + "RF603HS CONNECTION TEST")
    print("="*70)

    # Список портов
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("\n❌ Нет доступных COM-портов!")
        return

    print("\nДоступные COM-порты:")
    print("-"*70)
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   Описание: {port.description}")
        print(f"   HWID: {port.hwid}")
        print("-"*70)

    # Выбор порта
    try:
        choice = int(input(f"\nВыберите порт (1-{len(ports)}): "))
        if choice < 1 or choice > len(ports):
            raise ValueError

        selected_port = ports[choice - 1].device

    except (ValueError, IndexError):
        print("❌ Неверный выбор!")
        return

    # Тестируем разные скорости
    print("\n" + "="*70)
    print("АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ СКОРОСТЕЙ")
    print("="*70)

    baudrates = [9600, 19200, 57600, 115200, 460800]
    success = False

    for baudrate in baudrates:
        if test_port(selected_port, baudrate):
            success = True
            print(f"\n✅ Успешное подключение на скорости {baudrate} бод")
            break
        else:
            print(f"\n⚠️ Не удалось подключиться на скорости {baudrate} бод")
            time.sleep(0.5)

    if not success:
        print("\n" + "="*70)
        print("❌ НЕ УДАЛОСЬ ПОДКЛЮЧИТЬСЯ НИ НА ОДНОЙ СКОРОСТИ")
        print("="*70)
        print("\nВозможные причины:")
        print("1. Датчик не подключен или не включен")
        print("2. Неверный COM-порт")
        print("3. Проблемы с кабелем")
        print("4. Датчик требует нестандартную настройку")
        print("\nПопробуйте:")
        print("- Проверить питание датчика (9-36В)")
        print("- Проверить правильность подключения проводов")
        print("- Перезапустить датчик")
        print("- Использовать программу от производителя для настройки")

    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
        sys.exit(0)
