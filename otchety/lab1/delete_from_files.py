def files_criteria(input, criteria, output):
    stop_words_set = set()
    try:
        with open(criteria, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    stop_words_set.add(word)
    except FileNotFoundError:
        print(f"Файл стоп-слов '{criteria}' не найден.")
        return

    try:
        with open(input, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Файл частот '{input}' не найден.")
        return

    cleaned_lines = []
    total_words = 0
    removed_count = 0

    for line in lines:
        if "|" in line:
            parts = line.split('|')
            if len(parts) == 2:
                total_words += 1
                word_in_dict = parts[0].strip().lower()

                if word_in_dict in stop_words_set:
                    removed_count += 1
                    continue

        cleaned_lines.append(line)

    with open(output, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

    percent = (removed_count / total_words * 100) if total_words > 0 else 0

    print(f"Всего слов: {total_words}")
    print(f"Удалено: {removed_count} ({percent:.2f}%)")
    print(f"Результат: {output}\n")