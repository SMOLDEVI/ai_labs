import os
import re


def process_text_data(input_directory, merged_filename, result_filename):

    full_content = ""
    print(f" Чтение файлов из папки: {input_directory} ")

    if not os.path.exists(input_directory):
        print(f"Ошибка: Директория '{input_directory}' не найдена.")
        return

    files = os.listdir(input_directory)

    for filename in files:
        if filename.endswith(".txt"):
            file_path = os.path.join(input_directory, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    full_content += content + " "
                print(f"Файл {filename} успешно прочитан.")
            except Exception as e:
                print(f"Ошибка при чтении {filename}: {e}")

    with open(merged_filename, 'w', encoding='utf-8') as f:
        f.write(full_content)
    print(f"\nОбъединенный текст сохранен в '{merged_filename}'")


    text_lower = full_content.lower()

    pattern = r'[^а-яё\s]'

    normalized_text = re.sub(pattern, ' ', text_lower)

    normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()

    words_list = normalized_text.split()
    word_counts = {}

    for word in words_list:
        word_counts[word] = word_counts.get(word, 0) + 1

    sorted_items = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)

    with open(result_filename, 'w', encoding='utf-8') as f:
        f.write("Слово | Частота\n")
        f.write("-" * 20 + "\n")
        for word, count in sorted_items:
            f.write(f"{word}: {count}\n")

    print(f"\nАнализ завершен. Результаты сохранены в '{result_filename}'")

    print("\nТоп-5 частых слов:")
    for word, count in sorted_items[:5]:
        print(f"{word}: {count}")


if __name__ == "__main__":
    INPUT_DIR = 'input_data'
    MERGED_FILE = 'merged_text.txt'
    RESULT_FILE = 'frequency_analysis.txt'  

    process_text_data(INPUT_DIR, MERGED_FILE, RESULT_FILE)