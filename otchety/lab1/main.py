from files_merger import merge_files
from file_cleaner import clean_file
from dictionary_frequency import get_frequency_map
from stop_word_criteria import my_criteria
from delete_from_files import files_criteria
from libs_criteria import compare_libraries

if __name__ == "__main__":

    INPUT_DIR = 'input_data'
    STOP_WORD_DIR = 'stop_words'

    MERGED_TEXT_FILE = 'merged_text.txt'
    MERGED_STOP_WORDS_FILE = 'merged_stop_words.txt'
    CLEAN_TEXT_FILE = "clean_text_source.txt"

    FREQ_FILE_ORIGINAL = "freq_original.txt"
    FREQ_FILE_LOWER = "freq_lower_case.txt"

    RESULT_MY_CRITERIA = 'result_1_my_rules.txt'
    RESULT_FROM_FILE = "result_2_from_file.txt"
    RESULT_NLTK = 'result_3_nltk.txt'
    RESULT_SPACY = 'result_3_spacy.txt'

    print("=== ЗАПУСК ОБРАБОТКИ ДАННЫХ ===\n")

    print("1. Объединение файлов...")
    merge_files(INPUT_DIR, MERGED_TEXT_FILE)
    merge_files(STOP_WORD_DIR, MERGED_STOP_WORDS_FILE)

    print("2. Очистка текста от символов...")
    clean_file(MERGED_TEXT_FILE, CLEAN_TEXT_FILE)

    print("3. Генерация частотных словарей...")
    get_frequency_map(CLEAN_TEXT_FILE, FREQ_FILE_ORIGINAL, FREQ_FILE_LOWER)

    print("\n--- ЭТАП ФИЛЬТРАЦИИ (3 ПОДХОДА) ---")

    print(f"А. Применяем свои критерии (результат в {RESULT_MY_CRITERIA})...")
    my_criteria(FREQ_FILE_LOWER, RESULT_MY_CRITERIA)

    print(f"Б. Удаляем по файлу стоп-слов (результат в {RESULT_FROM_FILE})...")
    files_criteria(FREQ_FILE_LOWER, MERGED_STOP_WORDS_FILE, RESULT_FROM_FILE)

    print(f"В. Сравниваем библиотеки NLTK и spaCy...")
    compare_libraries(FREQ_FILE_LOWER, RESULT_NLTK, RESULT_SPACY)

