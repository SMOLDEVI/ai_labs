import binascii


def get_shingles(text, shingle_size):
    # Разбивает текст на шинглы заданной длины
    words = text.split()
    shingles = []
    for i in range(len(words) - shingle_size + 1):
        shingle = ' '.join(words[i:i + shingle_size])
        shingles.append(shingle)
    return shingles


def calculate_crc32(shingles):
    #  Вычисляет CRC32 хэши для списка шинглов"
    hashes = []
    for shingle in shingles:
        hash_val = binascii.crc32(shingle.encode('utf-8')) & 0xFFFFFFFF
        hashes.append(hash_val)
    return hashes


def calculate_originality(text1, text2, shingle_size):
    # Вычисляет оригинальность первого текста относительно второго
    shingles1 = get_shingles(text1, shingle_size)
    shingles2 = get_shingles(text2, shingle_size)

    hashes1 = calculate_crc32(shingles1)
    hashes2 = calculate_crc32(shingles2)

    sovpad = [h for h in hashes1 if h in hashes2]
    original = 100 - (len(sovpad) / len(hashes1)) * 100

    return original


# Загружаем тексты из файлов
with open('text1.txt', 'r', encoding='utf-8') as f:
    text_orig = f.read()  # оригинальный текст

with open('text2.txt', 'r', encoding='utf-8') as f:
    text_prov = f.read()  # проверяемый текст

# ТАБЛИЦА ЗАВИСИМОСТИ ОТ ДЛИНЫ ШИНГЛА
print("Таблица зависимости оригинальности от длины шингла")
print("Длина шингла  | Оригинальность (%)")

razmery = [2, 3, 4, 5, 6, 8]
for razmer in razmery:
    orig_procent = calculate_originality(text_orig, text_prov, razmer)
    print(f"      {razmer}       |      {orig_procent:.2f}")

print()


print("Результат для шага шингла = 3")

shag = 3

# Получаем шинглы и их хэши
shingles_orig = get_shingles(text_orig, shag)
shingles_prov = get_shingles(text_prov, shag)

hashes_orig = calculate_crc32(shingles_orig)
hashes_prov = calculate_crc32(shingles_prov)

# Находим совпадающие и уникальные хэши
obschie = [h for h in hashes_orig if h in hashes_prov]  # общие для обоих текстов
unikalnye = [h for h in hashes_orig if h not in hashes_prov]  # только в первом тексте

# Вычисляем оригинальность
orig_procent = 100 - (len(obschie) / len(hashes_orig)) * 100

# Выводим результаты
print("Контрольные суммы шинглов первого текста:")
print(hashes_orig)

print("\nКонтрольные суммы шинглов второго текста:")
print(hashes_prov)

print("\nОтличительные значения (уникальные для первого текста):")
print(unikalnye)

print(f"\nОбщее количество шинглов в тексте: {len(hashes_orig)}")
print(f"Количество шинглов, совпадающих со вторым текстом: {len(obschie)}")
print(f"Количество шинглов, уникальных для первого текста: {len(unikalnye)}")
print(f"Проверка: {len(obschie)} + {len(unikalnye)} = {len(obschie) + len(unikalnye)}")
print(f"\nОригинальность текста: {orig_procent:.2f}%")

