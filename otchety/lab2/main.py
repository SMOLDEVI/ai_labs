import os
import re
import math
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
import pymorphy2
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

nltk.download('stopwords', quiet=True)

stop_words = set(stopwords.words('russian'))
stemmer = SnowballStemmer('russian')
morph = pymorphy2.MorphAnalyzer()

def load_docs(folder, limit=None):
    files = [f for f in os.listdir(folder) if f.endswith(".txt")]
    if limit:
        files = files[:limit]

    docs = []
    good_files = []

    for f in files:
        path = os.path.join(folder, f)

        for enc in ("utf-8", "cp1251"):
            try:
                with open(path, encoding=enc) as file:
                    docs.append(file.read())
                    good_files.append(f)
                break
            except:
                continue
        else:
            print(f"Не удалось прочитать файл: {f}")
    return docs, good_files

def clean_text(text):
    text = re.sub(r'[^а-яё\s]', ' ', text.lower())
    text = re.sub(r'\s+', ' ', text).strip()
    return [w for w in text.split() if w not in stop_words]

def normalize(words, method):
    if method == "stem":
        return [stemmer.stem(w) for w in words]
    elif method == "lemma":
        return [morph.parse(w)[0].normal_form for w in words]
    return words

def compute_idf(corpus_folder):
    docs, _ = load_docs(corpus_folder)
    corpus = [clean_text(d) for d in docs]
    D = len(corpus)
    df = {}
    for doc in corpus:
        for word in set(doc):
            df[word] = df.get(word, 0) + 1

    return df, D

def analyze_doc(words, df, D):
    total = len(words)
    counter = Counter(words)
    top5 = counter.most_common(5)
    result = []
    for word, count in top5:
        tf = count / total
        idf = math.log(D / df.get(word, 1))
        tfidf = tf * idf
        result.append((word, tf, idf, tfidf))
    return result

def print_table(before, after, title):
    print("\n" + "=" * 100)
    print(f"{title:^100}")
    print("=" * 100)
    print(f'{"ДО":<30}|{"ПОСЛЕ":<45}')
    print("-" * 100)
    for i in range(5):
        w1, tf1, idf1, tfidf1 = before[i]
        w2, tf2, idf2, tfidf2 = after[i]
        print(f"{w1:<10} {tf1:.3f} {idf1:.3f} {tfidf1:.3f} | "
              f"{w2:<10} {tf2:.3f} {idf2:.3f} {tfidf2:.3f}")

def show_wordcloud(words, filename, title):
    text = " ".join(words)
    cloud = WordCloud(width=800, height=400, background_color="white").generate(text)
    cloud.to_file(filename)
    plt.figure()
    plt.imshow(cloud)
    plt.axis("off")
    plt.title(title)
    plt.show()

def evaluate(docs_words, df, D):
    vocab = set()
    tfidf_sum = 0
    count = 0
    for words in docs_words:
        res = analyze_doc(words, df, D)
        vocab.update(words)
        for r in res:
            tfidf_sum += r[3]
            count += 1
    avg_tfidf = tfidf_sum / count if count else 0
    return len(vocab), avg_tfidf

def main():
    raw_docs, filenames = load_docs("texts", limit=3)

    # 2. IDF по ВСЕМ документам
    df, D = compute_idf("texts")

    before_all = []
    lemma_all = []
    stem_all = []

    for doc in raw_docs:
        words = clean_text(doc)

        before_all.append(words)
        lemma_all.append(normalize(words, "lemma"))
        stem_all.append(normalize(words, "stem"))

    # 3. Оценка методов
    vocab_lemma, tfidf_lemma = evaluate(lemma_all, df, D)
    vocab_stem, tfidf_stem = evaluate(stem_all, df, D)

    print("\n=== СРАВНЕНИЕ МЕТОДОВ (по 3 текстам) ===")
    print(f"Лемматизация: словарь={vocab_lemma}, TF-IDF={tfidf_lemma:.4f}")
    print(f"Стемминг:     словарь={vocab_stem}, TF-IDF={tfidf_stem:.4f}")

    best_method = "lemma" if (vocab_lemma < vocab_stem) else "stem"
    print(f"\nЛУЧШИЙ МЕТОД: {best_method}")

    # 4. По каждому тексту
    for i in range(3):
        before = analyze_doc(before_all[i], df, D)

        if best_method == "lemma":
            after_words = lemma_all[i]
        else:
            after_words = stem_all[i]

        after = analyze_doc(after_words, df, D)

        # таблица
        print_table(before, after, f"Документ {i+1}: {filenames[i]}")

        # облака
        show_wordcloud(before_all[i], f"before_{i}.png", f"До {i+1}")
        show_wordcloud(after_words, f"after_{i}.png", f"После {i+1}")


if __name__ == "__main__":
    main()
