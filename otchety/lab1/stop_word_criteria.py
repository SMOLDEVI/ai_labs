def my_criteria(input_freq_file, output_file):
    try:
        with open(input_freq_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Файл не найден.")
        return

    result_lines = []
    total_words = 0
    removed_count = 0

    for line in lines:
        if "|" in line:
            parts = line.split('|')
            if len(parts) == 2:
                word = parts[0].strip()
                count_str = parts[1].strip()

                if count_str.isdigit():
                    total_words += 1

                    if len(word) <= 3:
                        removed_count += 1
                        continue

        result_lines.append(line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    percent = (removed_count / total_words * 100) if total_words > 0 else 0

    print(f"Всего слов: {total_words}")
    print(f"Удалено: {removed_count} ({percent:.2f}%)")
    print(f"Результат: {output_file}\n")