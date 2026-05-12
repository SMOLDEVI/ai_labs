import cv2
import numpy as np
import matplotlib.pyplot as plt

def custom_convolve(image, kernel):
    k_h, k_w = kernel.shape
    pad_h, pad_w = k_h // 2, k_w // 2
    
    padded_img = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')
    output = np.zeros_like(image, dtype=np.float32)
    
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            window = padded_img[y:y+k_h, x:x+k_w]
            output[y, x] = np.sum(window * kernel)
            
    return output

def part_one():
    img_name = input("Введите имя исходной картинки: ") or "image.jpg"
    img_color = cv2.imread(img_name)
    
    if img_color is None:
        print(f"❌ Ошибка: не удалось загрузить '{img_name}'. Проверь файл!")
        return

    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    
    # 1. Сначала ГИСТОГРАММА (показываем и закрываем)
    img_blur_lib_5x5 = cv2.GaussianBlur(img_gray, (5, 5), 0)
    
    plt.figure(figsize=(10, 5))
    plt.hist(img_gray.ravel(), bins=256, range=[0, 256], color='blue', alpha=0.5, label='Исходное ЧБ')
    plt.hist(img_blur_lib_5x5.ravel(), bins=256, range=[0, 256], color='red', alpha=0.5, label='Сглаженное (Gaussian 5x5)')
    plt.title('Гистограммы яркости')
    plt.legend()
    plt.show() # Здесь программа остановится, пока ты не закроешь окно графика КРЕСТИКОМ

    # 2. Потом CV2 окна
    gaussian_kernel_3x3 = np.array([[1, 2, 1], 
                                    [2, 4, 2], 
                                    [1, 2, 1]], dtype=np.float32) / 16.0
    
    gauss_manual_3x3 = custom_convolve(img_gray, gaussian_kernel_3x3)
    gauss_manual_3x3 = np.clip(gauss_manual_3x3, 0, 255).astype(np.uint8) 
    
    laplace_kernel_3x3 = np.array([[0,  1, 0],
                                   [1, -4, 1],
                                   [0,  1, 0]], dtype=np.float32)
    
    laplace_manual = custom_convolve(img_gray, laplace_kernel_3x3)
    laplace_manual = np.absolute(laplace_manual)
    laplace_manual = np.clip(laplace_manual, 0, 255).astype(np.uint8)
    
    laplace_lib = cv2.Laplacian(img_gray, cv2.CV_64F, ksize=3)
    laplace_lib = np.absolute(laplace_lib)
    laplace_lib = np.clip(laplace_lib, 0, 255).astype(np.uint8)

    cv2.imshow('1. Original Gray', img_gray)
    cv2.imshow('2. Gauss Manual (3x3)', gauss_manual_3x3)
    cv2.imshow('3. Gauss Library (5x5)', img_blur_lib_5x5)
    cv2.imshow('4. Laplace Manual (3x3)', laplace_manual)
    cv2.imshow('5. Laplace Library (3x3)', laplace_lib)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def manual_thinning(img_bin):
    # Классический алгоритм морфологического утончения (скелетизации).
    # Утончает до 1 пикселя, но оставляет артефакты ("бахрому" на углах).
    # Идеально подходит под требования преподавателя!
    skel = np.zeros(img_bin.shape, np.uint8)
    img = img_bin.copy()
    # Крестообразное ядро 3х3
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    
    while True:
        # Шаг 1: Эрозия
        eroded = cv2.erode(img, element)
        # Шаг 2: Дилатация эродированного
        temp = cv2.dilate(eroded, element)
        # Шаг 3: Вычитание (находим пиксели скелета на этом шаге)
        temp = cv2.subtract(img, temp)
        # Шаг 4: Добавляем к итоговому скелету
        skel = cv2.bitwise_or(skel, temp)
        # Шаг 5: Перезаписываем исходник для следующей итерации
        img = eroded.copy()
        
        # Если картинка стала полностью черной - мы закончили
        if cv2.countNonZero(img) == 0:
            break
            
    return skel

def part_two(image_path):
    img_letter = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_letter is None:
        print(f"❌ Ошибка: не удалось загрузить '{image_path}'. Проверь название и формат!")
        return

    # Сглаживаем фон
    blurred = cv2.GaussianBlur(img_letter, (5, 5), 0)
    
    # Бинаризация (жесткий порог)
    _, binary = cv2.threshold(blurred, 125, 255, cv2.THRESH_BINARY_INV)
    
    # Ручное утончение (оставит ту самую "бахрому" по методичке)
    thinned_manual = manual_thinning(binary)
    
    # Библиотечное утончение (Эрозия)
    # По методичке (стр 6) используем ядро 5х5. 
    # Количество итераций я поставил 5 (будет видно, как буква сильно похудела). 
    # Если буква исчезнет полностью - уменьши iterations до 3.
    kernel_erode = np.ones((5, 5), np.uint8)
    thinned_lib = cv2.erode(binary, kernel_erode, iterations=5)

    print(f"✅ Обработана картинка {image_path}. Нажми любую клавишу в окне, чтобы закрыть.")
    cv2.imshow(f'Original: {image_path}', img_letter)
    cv2.imshow(f'Binarized', binary)
    cv2.imshow(f'Manual Thinning (With artifacts)', thinned_manual)
    cv2.imshow(f'Library Thinning (Erosion)', thinned_lib)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def part_two(image_path):
    img_letter = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_letter is None:
        print(f"❌ Ошибка: не удалось загрузить '{image_path}'. Проверь название и формат!")
        return

    blurred = cv2.GaussianBlur(img_letter, (5, 5), 0)
    
    _, binary = cv2.threshold(blurred, 125, 255, cv2.THRESH_BINARY_INV)
    
    binary_smoothed = cv2.medianBlur(binary, 9) 
    
    thinned_manual = manual_thinning(binary_smoothed)
    
    kernel_erode = np.ones((5, 5), np.uint8)
    thinned_lib = cv2.erode(binary_smoothed, kernel_erode, iterations=5)

    print(f"✅ Обработана картинка {image_path}. Нажми любую клавишу в окне, чтобы закрыть.")
    cv2.imshow(f'Original: {image_path}', img_letter)
    cv2.imshow(f'Binarized', binary_smoothed)  # Показываем уже приглаженную букву
    cv2.imshow(f'Manual Thinning (With artifacts)', thinned_manual)
    cv2.imshow(f'Library Thinning (Erosion)', thinned_lib)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    while True:
        print("1 - Запустить Часть 1 (Гаусс, Лаплас, Гистограммы)")
        print("2 - Запустить Часть 2 (Утончение контуров букв)")
        print("0 - Выход из программы")
        
        choice = input("👉 Выбери действие (0, 1, 2): ").strip()
        
        if choice == '1':
            part_one()
            
        elif choice == '2':
            img_path = input("введи название картинки с расширением: ").strip()
            part_two(img_path)
            
        elif choice == '0':
            break
            
        else:
            print(" Неверный ввод!")
