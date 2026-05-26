import nltk
from nltk.corpus import stopwords
from spacy.lang.ru import Russian

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def compare_libraries(input_file, out_nltk, out_spacy):
    nltk_stops = set(stopwords.words('russian'))
    nlp = Russian()
    spacy_stops = nlp.Defaults.stop_words

    print(f"База NLTK: {len(nltk_stops)} слов.")
    print(f"База spaCy: {len(spacy_stops)} слов.")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Файл не найден.")
        return

    lines_nltk = []
    lines_spacy = []

    total_words = 0
    removed_count_nltk = 0
    removed_count_spacy = 0

    for line in lines:
        if "|" in line:
            parts = line.split('|')
            if len(parts) == 2:
                total_words += 1
                word = parts[0].strip().lower()

                if word in nltk_stops:
                    removed_count_nltk += 1
                else:
                    lines_nltk.append(line)

                if word in spacy_stops:
                    removed_count_spacy += 1
                else:
                    lines_spacy.append(line)
            else:
                lines_nltk.append(line)
                lines_spacy.append(line)
        else:
            lines_nltk.append(line)
            lines_spacy.append(line)

    with open(out_nltk, 'w', encoding='utf-8') as f:
        f.writelines(lines_nltk)

    with open(out_spacy, 'w', encoding='utf-8') as f:
        f.writelines(lines_spacy)

    percent_nltk = (removed_count_nltk / total_words * 100) if total_words > 0 else 0
    percent_spacy = (removed_count_spacy / total_words * 100) if total_words > 0 else 0

    print(f"Всего слов: {total_words}")
    print(f"NLTK удалил:  {removed_count_nltk} строк ({percent_nltk:.2f}%)")
    print(f"spaCy удалил: {removed_count_spacy} строк ({percent_spacy:.2f}%)\n")