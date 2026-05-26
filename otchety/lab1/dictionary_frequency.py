import os


def get_frequency_map(input_filename, output_original, output_lower):
    if not os.path.exists(input_filename):
        print(f"Файл '{input_filename}' не найден.")
        return

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return

    if not text.strip():
        print("Файл пуст")
        return

    words = text.split()

    frequency_dict_original = {}
    frequency_dict_lower = {}

    for word in words:
        # Оригинал
        if word in frequency_dict_original:
            frequency_dict_original[word] += 1
        else:
            frequency_dict_original[word] = 1

        word_lower = word.lower()
        if word_lower in frequency_dict_lower:
            frequency_dict_lower[word_lower] += 1
        else:
            frequency_dict_lower[word_lower] = 1

    sorted_original = sorted(frequency_dict_original.items(), key=lambda item: item[1], reverse=True)
    sorted_lower = sorted(frequency_dict_lower.items(), key=lambda item: item[1], reverse=True)

    with open(output_original, 'w', encoding='utf-8') as f:

        f.write(f"{'СЛОВО':<15} | {'ЧАСТОТА'}\n")
        for word, count in sorted_original:
            f.write(f"{word:<15} | {count}\n")

    print(f"Файл 1 сохранен: {output_original}")

    with open(output_lower, 'w', encoding='utf-8') as f:
        f.write(f"{'СЛОВО':<15} | {'ЧАСТОТА'}\n")
        for word, count in sorted_lower:
            f.write(f"{word:<15} | {count}\n")

    print(f"Файл 2 сохранен: {output_lower}")
