import re


def normalize_text(text):
    #lower_text = text.lower()
    cleaned_text = re.sub(r'[^а-яё\^А-ЯЁ\s]', ' ', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text


def clean_file(input, out):
    try:
        with open(input, 'r', encoding='utf-8') as f:
            content = f.read()

        normalized = normalize_text(content)

        with open(out, 'w', encoding='utf-8') as f:
            f.write(normalized)

            print(f"чистый файл {out}")
        return normalized
    except FileNotFoundError:
        print(f"Файл {input} не найден.")
        return None