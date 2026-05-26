import os
import shutil


def merge_files(source_dir, output_filename):
    if not os.path.exists(source_dir):
        print(f"Папка {source_dir} не найдена.")
        return False
    files = sorted(os.listdir(source_dir))

    with open(output_filename, 'w', encoding='utf-8') as f:
        for filename in files:
            if not filename.endswith(".txt"):
                continue

            file_path = os.path.join(source_dir, filename)
            source_file = None
            try:
                source_file = open(file_path, 'r', encoding='utf-8')
                source_file.read(1)
                source_file.seek(0)
            except UnicodeDecodeError:
                if source_file: source_file.close()
                source_file = open(file_path, 'r', encoding='cp1251')
            except Exception as e:
                print(f"Ошибка с файлом {filename}: {e}")
                continue

            if source_file:
                shutil.copyfileobj(source_file, f)
                f.write("\n")
                source_file.close()
                print(f"Файл '{filename}' добавлен.")

    print(f"Результат: {output_filename}\n")
    return True
