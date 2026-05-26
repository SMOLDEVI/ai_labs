import os
import spacy
from spacy import displacy
from pathlib import Path
from spacy.tokens import Span

try:
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()
except ImportError:
    import os
    os.system("pip install pymorphy3")
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()

try:
    nlp = spacy.load("ru_core_news_lg")
except:
    os.system("python -m spacy download ru_core_news_lg")
    nlp = spacy.load("ru_core_news_lg")


def fix_entity_types(doc, corrections):
    entities = list(doc.ents)
    new_entities = []

    for ent in entities:
        if ent.text in corrections:
            new_ent = Span(doc, ent.start, ent.end, label=corrections[ent.text])
            new_entities.append(new_ent)
        else:
            new_entities.append(ent)

    doc.ents = new_entities
    return doc


def visualize_displacy(doc, style="dep", filename=None, title="Визуализация"):
    options = {
        "compact": True,
        "bg": "white",
        "color": "black",
        "font": "Source Sans Pro",
        "distance": 130,
        "arrow_stroke": 2,
        "arrow_width": 6,
    }

    html = displacy.render(doc, style=style, options=options, page=True)
    style_fix = '<meta charset="UTF-8">'
    html = html.replace("<title>displaCy</title>", f"<title>{title}</title>")

    if "</head>" in html:
        html = html.replace("</head>", style_fix + "</head>")
    else:
        html = html.replace("<html>", "<html><head>" + style_fix + "</head>")

    if filename:
        Path(filename).write_text(html, encoding='utf-8')
        print(f"Визуализация сохранена: {filename}")
    else:
        displacy.render(doc, style=style, options=options)


def swap_verb_to_2nd_person(verb_word: str) -> str:
    """Приводит глагол 1-го лица к форме 2-го лица единственного числа."""
    overrides = {
        "могу": "можешь",
        "хочу": "хочешь",
        "буду": "будешь",
        "ем": "ешь",
        "дам": "дашь",
        "знаю": "знаешь",
        "думаю": "думаешь",
        "обещаю": "обещаешь",
    }
    lowered = verb_word.lower()
    if lowered in overrides:
        res = overrides[lowered]
        return res.upper() if verb_word.isupper() else (res.capitalize() if verb_word.istitle() else res)

    parsed = morph.parse(verb_word)
    for p in parsed:
        if 'VERB' in p.tag:
            if '1per' in p.tag and 'sing' in p.tag:
                inflected = p.inflect({'2per', 'sing'})
                if inflected:
                    return inflected.word
    return verb_word


def swap_verb_to_1st_person(verb_word: str) -> str:
    """Приводит глагол 2-го лица к форме 1-го лица единственного числа."""
    overrides = {
        "можешь": "могу",
        "хочешь": "хочу",
        "будешь": "буду",
        "ешь": "ем",
        "дашь": "дам",
        "знаешь": "знаю",
        "думаешь": "думаю",
        "обещаешь": "обещаю",
    }
    lowered = verb_word.lower()
    if lowered in overrides:
        res = overrides[lowered]
        return res.upper() if verb_word.isupper() else (res.capitalize() if verb_word.istitle() else res)

    parsed = morph.parse(verb_word)
    for p in parsed:
        if 'VERB' in p.tag:
            if '2per' in p.tag and 'sing' in p.tag:
                inflected = p.inflect({'1per', 'sing'})
                if inflected:
                    return inflected.word
    return verb_word


def affirmative_to_question(text: str) -> str:
    doc = nlp(text)

    # Словарь взаимной замены местоимений
    pronoun_swaps = {
        "я": "ты", "ты": "я",
        "мне": "тебе", "тебе": "мне",
        "меня": "тебя", "тебя": "меня",
        "мной": "тобой", "тобой": "мной",
        "мною": "тобою", "тобою": "мною",
        "мы": "вы", "вы": "мы",
        "нам": "вам", "вам": "нам",
        "нас": "вас", "вас": "нас",
        "наш": "ваш", "ваш": "наш",
        "мой": "твой", "твой": "мой",
        "моего": "твоего", "твоего": "моего",
        "моя": "твоя", "твоя": "моя",
        "мое": "твое", "твое": "мое",
        "моё": "твоё", "твоё": "моё",
        "мои": "твои", "твои": "мои",
        "моих": "твоих", "твоих": "моих",
        "моим": "твоим", "твоим": "моим",
        "моими": "твоими", "твоими": "моими"
    }

    # Поиск местоимений первого лица для определения необходимости изменения роли
    has_1st_person = False
    for token in doc:
        if token.text.lower() in ["я", "мне", "меня", "мы", "нам", "нас"]:
            has_1st_person = True
            break

    processed_tokens = []

    for token in doc:
        word = token.text
        lowered = word.lower()

        # 1. Замена личных и притяжательных местоимений
        if lowered in pronoun_swaps:
            swap = pronoun_swaps[lowered]
            if word.isupper():
                word = swap.upper()
            elif word.istitle():
                word = swap.capitalize()
            else:
                word = swap

        # 2. Корректировка глаголов главного предложения
        elif token.pos_ in ["VERB", "AUX"]:
            # Проверяем, относится ли глагол к главной структуре предложения (ROOT или его непосредственная связь)
            is_main_verb = (token.dep_ == "ROOT" or token.head.dep_ == "ROOT" or token.head.head.dep_ == "ROOT")
            if is_main_verb:
                if has_1st_person:
                    word = swap_verb_to_2nd_person(token.text)
                elif lowered in ["хочешь", "можешь", "знаешь", "думаешь", "делаешь"]:
                    word = swap_verb_to_1st_person(token.text)

        processed_tokens.append((word, token.whitespace_))

    # Стилистическая перестановка для классических вопросов с модальными глаголами ("Ты можешь..." -> "Можешь ли ты...")
    if len(processed_tokens) > 1:
        w0, ws0 = processed_tokens[0]
        w1, ws1 = processed_tokens[1]
        if w0.lower() == "ты" and w1.lower() in ["можешь", "хочешь", "будешь", "должен", "знаешь", "обещаешь"]:
            processed_tokens[0] = (w1.capitalize(), " ")
            processed_tokens[1] = (f"ли ты", ws1)

    # Если в предложении не было местоимений 1-го лица, строим вопрос через оборот "<глагол> ли <подлежащее>...?"
    elif not has_1st_person and len(doc) > 1:
        if doc[0].dep_ == "nsubj" and doc[1].dep_ == "ROOT" and doc[1].pos_ in ["VERB", "AUX"]:
            subj_token = doc[0]
            subject_text = processed_tokens[0][0]
            root_text = processed_tokens[1][0]
            ws1 = processed_tokens[1][1]

            # Сохраняем регистр имени собственного (например, "Иван" / "Москва")
            if subj_token.pos_ != "PROPN" and not subj_token.text.isupper():
                subject_text_formatted = subject_text.lower()
            else:
                subject_text_formatted = subject_text

            processed_tokens[0] = (root_text.capitalize(), " ")
            processed_tokens[1] = (f"ли {subject_text_formatted}", ws1)
        else:
            # Универсальный fallback-вариант с частицей "Разве"
            w0, ws0 = processed_tokens[0]
            if doc[0].pos_ != "PROPN":
                processed_tokens[0] = (w0.lower(), ws0)
            processed_tokens.insert(0, ("Разве", " "))

    # Сборка предложения с сохранением исходных пробелов и знаков препинания
    question = "".join(w + ws for w, ws in processed_tokens).strip()

    # Замена финальной точки на вопросительный знак
    question = question.rstrip(".!? ") + "?"

    return question


def run_lab():
    print("\nЗАДАНИЕ 1: РАЗМЕТКА ЧАСТЕЙ РЕЧИ И СИНТАКСИЧЕСКИХ ЗАВИСИМОСТЕЙ")
    print("-" * 70)

    sentences = [
        "Я могу обещать, что это стоит твоего времени.",
        "Иван купил новую красную машину в Москве.",
        "Москва является столицей России."
    ]

    for idx, sentence in enumerate(sentences, 1):
        print(f"\n--- Предложение {idx}: {sentence} ---")
        doc = nlp(sentence)
        print(f"{'Токен':<12} | {'POS':<8} | {'Зависимость':<12} | {'Главное слово'}")
        print("-" * 55)
        for token in doc:
            print(f"{token.text:<12} | {token.pos_:<8} | {token.dep_:<12} | {token.head.text}")

    print("\n\nЗАДАНИЕ 2: ВИЗУАЛИЗАЦИЯ С ПОМОЩЬЮ DISPLACY")
    print("-" * 70)

    print("\n--- 2.1 Визуализация деревьев зависимостей (style='dep') ---")
    for idx, sentence in enumerate(sentences, 1):
        doc = nlp(sentence)
        filename = f"dep_tree_{idx}.html"
        visualize_displacy(doc, style="dep", filename=filename, title=f"Дерево зависимостей: {sentence[:30]}...")

    print("\n--- 2.2 Визуализация именованных сущностей (style='ent') ---")
    ner_text = """Компании Google, Яндекс и Сбер являются лидерами в области искусственного интеллекта. 
В 2007 году Себастьян Трун начал работать над самоуправляемыми автомобилями в Google. 
В марте 2025 года Яндекс и Сбер открыли новый центр искусственного интеллекта в Сколково. 
Генеральный директор Иван Петров выступил с докладом в Москве."""

    doc_ner = nlp(ner_text)

    corrections = {
        "Google": "ORG",
        "Яндекс": "ORG",
        "Сбер": "ORG",
        "Себастьян Трун": "PERSON",
        "Иван Петров": "PERSON",
        "Сколково": "GPE",
        "Москве": "GPE",
        "2007": "DATE",
        "2025": "DATE",
        "марте 2025 года": "DATE"
    }

    doc_ner = fix_entity_types(doc_ner, corrections)
    visualize_displacy(doc_ner, style="ent", filename="named_entities.html", title="Именованные сущности (NER)")

    print("\n--- 2.3 Визуализация с пользовательскими настройками цветов ---")
    colors = {
        "ORG": "linear-gradient(90deg, #aa9cfc, #fc9ce7)",
        "PERSON": "aqua",
        "GPE": "#09a3d5",
        "DATE": "lightgreen"
    }

    options = {"ents": ["ORG", "PERSON", "GPE", "DATE"], "colors": colors}
    html = displacy.render(doc_ner, style="ent", options=options, page=True)
    html = html.replace("<title>displaCy</title>", "<title>NER с кастомными цветами</title>")
    html = html.replace("</head>", '<meta charset="UTF-8"></head>')
    Path("ner_custom_colors.html").write_text(html, encoding='utf-8')
    print("Визуализация с кастомными цветами сохранена: ner_custom_colors.html")

    print("\n--- 2.4 Визуализация в ручном режиме (manual) ---")
    manual_data = {
        "words": [
            {"text": "Я", "tag": "PRON"},
            {"text": "хочу", "tag": "VERB"},
            {"text": "греческую", "tag": "ADJ"},
            {"text": "пиццу", "tag": "NOUN"}
        ],
        "arcs": [
            {"start": 0, "end": 1, "label": "nsubj", "dir": "left"},
            {"start": 2, "end": 3, "label": "amod", "dir": "left"},
            {"start": 1, "end": 3, "label": "dobj", "dir": "right"}
        ]
    }

    html_manual = displacy.render(manual_data, style="dep", manual=True, page=True)
    html_manual = html_manual.replace("<title>displaCy</title>", "<title>Ручная визуализация</title>")
    html_manual = html_manual.replace("</head>", '<meta charset="UTF-8"></head>')
    Path("manual_visualization.html").write_text(html_manual, encoding='utf-8')
    print("Ручная визуализация сохранена: manual_visualization.html")

    print("\n\nЗАДАНИЕ 3: КОНСОЛЬНЫЙ ДИАЛОГ")
    print("-" * 70)
    print("Введите утверждение на русском (или 'exit' для выхода).")

    while True:
        user_input = input("\nВы: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            print("До свидания!")
            break

        question = affirmative_to_question(user_input)
        print(f"Бот: {question}")


if __name__ == "__main__":
    run_lab()
