import cv2
import numpy as np
import matplotlib.pyplot as plt


def manual_grayscale(img):
    height, width, _ = img.shape
    gray = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            b = img[y, x][0]
            g = img[y, x][1]
            r = img[y, x][2]

            grey = 0.299 * r + 0.587 * g + 0.114 * b
            gray[y, x] = np.clip(grey, 0, 255)

    return gray


def add_noise(image):
    row, col = image.shape
    mean = 0
    sigma = 20
    gauss = np.random.normal(mean, sigma, (row, col))
    noisy = image + gauss
    return np.clip(noisy, 0, 255).astype(np.uint8)


def custom_convolve(image, kernel):
    k_h, k_w = kernel.shape
    pad_h = k_h // 2
    pad_w = k_w // 2

    padded = np.pad(
        image,
        ((pad_h, pad_h), (pad_w, pad_w)),
        mode='reflect'
    )

    output = np.zeros_like(image, dtype=np.float32)

    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            window = padded[y:y + k_h, x:x + k_w]
            output[y, x] = np.sum(window * kernel)

    return output


gauss_kernel_5x5 = np.array([
    [0.000789, 0.006581, 0.013347, 0.006581, 0.000789],
    [0.006581, 0.054901, 0.111345, 0.054901, 0.006581],
    [0.013347, 0.111345, 0.225821, 0.111345, 0.013347],
    [0.006581, 0.054901, 0.111345, 0.054901, 0.006581],
    [0.000789, 0.006581, 0.013347, 0.006581, 0.000789]
], dtype=np.float32)


laplace_kernel_1 = np.array([
    [0, 1, 0],
    [1, -4, 1],
    [0, 1, 0]
], dtype=np.float32)

laplace_kernel_2 = np.array([
    [1, 1, 1],
    [1, -8, 1],
    [1, 1, 1]
], dtype=np.float32)


def manual_thinning(img):
    work = (img > 0).astype(np.uint8)
    changed = True

    while changed:
        changed = False

        for side in ('B', 'H', 'L', 'P'):
            to_remove = []
            h, w = work.shape

            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    if work[y, x] == 0:
                        continue

                    p1 = work[y - 1, x - 1]
                    p2 = work[y - 1, x]
                    p3 = work[y - 1, x + 1]
                    p4 = work[y,     x - 1]
                    p5 = work[y,     x + 1]
                    p6 = work[y + 1, x - 1]
                    p7 = work[y + 1, x]
                    p8 = work[y + 1, x + 1]

                    n = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8
                    if n <= 1:
                        continue

                    if side == 'B':
                        phi = (p2 == 0 and p7 == 1)
                        f = ((not p3) and p4) or ((not p1) and p5) or (p4 and p5)
                    elif side == 'H':
                        phi = (p7 == 0 and p2 == 1)
                        f = ((not p8) and p4) or ((not p6) and p5) or (p4 and p5)
                    elif side == 'L':
                        phi = (p4 == 0 and p5 == 1)
                        f = ((not p1) and p7) or ((not p6) and p2) or (p2 and p7)
                    else:
                        phi = (p5 == 0 and p4 == 1)
                        f = ((not p3) and p7) or ((not p8) and p2) or (p2 and p7)

                    if phi and f:
                        to_remove.append((y, x))

            if to_remove:
                changed = True
                for yy, xx in to_remove:
                    work[yy, xx] = 0

    return (work * 255).astype(np.uint8)


def prune_skeleton(skel, iterations=5):
    work = (skel > 0).astype(np.uint8)
    original = work.copy()
    h, w = work.shape

    for _ in range(iterations):
        to_remove = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if work[y, x] == 0:
                    continue
                n = (work[y - 1, x - 1] + work[y - 1, x] + work[y - 1, x + 1] +
                     work[y,     x - 1]                  + work[y,     x + 1] +
                     work[y + 1, x - 1] + work[y + 1, x] + work[y + 1, x + 1])
                if n <= 1:
                    to_remove.append((y, x))
        if not to_remove:
            break
        for yy, xx in to_remove:
            work[yy, xx] = 0

    endpoints = np.zeros_like(work)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if work[y, x] == 0:
                continue
            n = (work[y - 1, x - 1] + work[y - 1, x] + work[y - 1, x + 1] +
                 work[y,     x - 1]                  + work[y,     x + 1] +
                 work[y + 1, x - 1] + work[y + 1, x] + work[y + 1, x + 1])
            if n == 1:
                endpoints[y, x] = 1

    for _ in range(iterations):
        new_ep = endpoints.copy()
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if endpoints[y, x] == 0:
                    continue
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        if original[y + dy, x + dx] == 1:
                            new_ep[y + dy, x + dx] = 1
        endpoints = new_ep

    result = work | (endpoints & original)
    return (result * 255).astype(np.uint8)


def opencv_skeleton(binary):
    img = binary.copy()
    skel = np.zeros(img.shape, np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while True:
        opened = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        temp = cv2.subtract(img, opened)
        eroded = cv2.erode(img, kernel)
        skel = cv2.bitwise_or(skel, temp)
        img = eroded.copy()

        if cv2.countNonZero(img) == 0:
            break

    return skel


def draw_labels(image, labels):
    for text, x, y in labels:
        (w, h), _ = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            2
        )
        cv2.rectangle(
            image,
            (x - 5, y - h - 5),
            (x + w + 5, y + 5),
            (0, 0, 0),
            -1
        )
        cv2.putText(
            image,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            255,
            2
        )


def part_one():
    img_name = input("Введите имя изображения: ") or "image_final.png"
    img_color = cv2.imread(img_name)

    if img_color is None:
        print("Ошибка загрузки изображения")
        return

    gray_manual = manual_grayscale(img_color)
    gray_library = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

    plt.figure(figsize=(12, 5))
    plt.hist(
        gray_manual.flatten(),
        bins=128,
        alpha=0.5,
        color='blue',
        label='Полутоновое вручную'
    )
    plt.hist(
        gray_library.flatten(),
        bins=128,
        alpha=0.5,
        color='red',
        label='Полутоновое библиотека'
    )
    plt.title("Сравнение полутоновых изображений")
    plt.legend()
    plt.show(block=False)
    plt.pause(0.001)

    noisy = add_noise(gray_manual)
    gauss_library_3x3 = cv2.GaussianBlur(noisy, (3, 3), 0)

    gauss_manual_5x5 = custom_convolve(noisy, gauss_kernel_5x5)
    gauss_manual_5x5 = np.clip(gauss_manual_5x5, 0, 255).astype(np.uint8)

    plt.figure(figsize=(12, 5))
    plt.hist(
        gauss_manual_5x5.flatten(),
        bins=128,
        alpha=0.5,
        color='green',
        label='Gauss Manual 5x5'
    )
    plt.hist(
        gauss_library_3x3.flatten(),
        bins=128,
        alpha=0.5,
        color='orange',
        label='Gauss Library 3x3'
    )
    plt.title("Сравнение фильтра Гаусса")
    plt.legend()
    plt.show(block=False)
    plt.pause(0.001)

    laplace_manual_1 = custom_convolve(gauss_manual_5x5, laplace_kernel_1)
    laplace_manual_1 = np.absolute(laplace_manual_1)
    laplace_manual_1 = np.clip(laplace_manual_1, 0, 255).astype(np.uint8)

    laplace_manual_2 = custom_convolve(gauss_manual_5x5, laplace_kernel_2)
    laplace_manual_2 = np.absolute(laplace_manual_2)
    laplace_manual_2 = np.clip(laplace_manual_2, 0, 255).astype(np.uint8)

    sobel = cv2.Sobel(gauss_manual_5x5, cv2.CV_64F, 1, 1, ksize=3)
    sobel = np.absolute(sobel)
    sobel = np.uint8(sobel)

    laplacian = cv2.Laplacian(gauss_manual_5x5, cv2.CV_64F)
    laplacian = np.absolute(laplacian)
    laplacian = np.uint8(laplacian)

    canny = cv2.Canny(gauss_manual_5x5, 100, 200)

    gabor_kernel_1 = cv2.getGaborKernel((21, 21), 4, 0, 10, 0.5, 0, ktype=cv2.CV_32F)
    gabor_kernel_2 = cv2.getGaborKernel((21, 21), 6, np.pi / 4, 15, 0.7, 0, ktype=cv2.CV_32F)
    gabor_kernel_3 = cv2.getGaborKernel((31, 31), 8, np.pi / 2, 20, 0.3, 0, ktype=cv2.CV_32F)

    gabor_f1 = cv2.filter2D(gauss_manual_5x5, cv2.CV_32F, gabor_kernel_1)
    gabor_f2 = cv2.filter2D(gauss_manual_5x5, cv2.CV_32F, gabor_kernel_2)
    gabor_f3 = cv2.filter2D(gauss_manual_5x5, cv2.CV_32F, gabor_kernel_3)

    gabor_1 = cv2.normalize(np.absolute(gabor_f1), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    gabor_2 = cv2.normalize(np.absolute(gabor_f2), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    gabor_3 = cv2.normalize(np.absolute(gabor_f3), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    img_size = (250, 250)

    row1 = np.hstack([
        cv2.resize(gray_manual, img_size),
        cv2.resize(gray_library, img_size),
        cv2.resize(noisy, img_size)
    ])

    row2 = np.hstack([
        cv2.resize(gauss_library_3x3, img_size),
        cv2.resize(gauss_manual_5x5, img_size),
        np.zeros((250, 250), dtype=np.uint8)
    ])

    row3 = np.hstack([
        cv2.resize(laplace_manual_1, img_size),
        cv2.resize(laplace_manual_2, img_size),
        cv2.resize(sobel, img_size)
    ])

    row4 = np.hstack([
        cv2.resize(laplacian, img_size),
        cv2.resize(canny, img_size),
        np.zeros((250, 250), dtype=np.uint8)
    ])

    final_window = np.vstack([row1, row2, row3, row4])

    labels = [
        ("Manual Gray", 20, 30),
        ("Library Gray", 270, 30),
        ("Noisy", 540, 30),
        ("Gauss Library 3x3", 20, 280),
        ("Gauss Manual 5x5", 270, 280),
        ("Laplace 4", 20, 530),
        ("Laplace 8", 270, 530),
        ("Sobel", 540, 530),
        ("Laplacian", 20, 780),
        ("Canny", 270, 780)
    ]

    draw_labels(final_window, labels)

    gabor_size = (300, 300)
    gabor_row = np.hstack([
        cv2.resize(gabor_1, gabor_size),
        cv2.resize(gabor_2, gabor_size),
        cv2.resize(gabor_3, gabor_size)
    ])

    gabor_labels = [
        ("sigma=4 theta=0 lambda=10 gamma=0.5", 10, 30),
        ("sigma=6 theta=PI/4 lambda=15 gamma=0.7", 310, 30),
        ("sigma=8 theta=PI/2 lambda=20 gamma=0.3", 610, 30)
    ]

    draw_labels(gabor_row, gabor_labels)

    cv2.imshow("LAB 6 - PART 1", final_window)
    cv2.imshow("GABOR FILTERS", gabor_row)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


def part_two():
    image_list = ["letter1.bmp", "letter2.bmp", "letter3.bmp", "letter4.bmp"]
    all_rows = []
    size = (250, 250)

    for img_path in image_list:
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"Ошибка загрузки {img_path}")
            continue

        blurred = cv2.GaussianBlur(img, (3, 3), 0)
        _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)

        binary_clean = cv2.medianBlur(binary, 5)
        binary_clean = cv2.morphologyEx(
            binary_clean, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)
        )
        binary_clean = cv2.morphologyEx(
            binary_clean, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)
        )
        binary_clean = cv2.medianBlur(binary_clean, 7)

        manual = manual_thinning(binary_clean)
        manual = cv2.dilate(manual, np.ones((3, 3), np.uint8), iterations=1)
        manual = manual_thinning(manual)
        manual = prune_skeleton(manual, iterations=5)

        library = opencv_skeleton(binary_clean)
        library = cv2.dilate(library, np.ones((3, 3), np.uint8), iterations=1)
        library = opencv_skeleton(library)
        library = prune_skeleton(library, iterations=5)

        row = np.hstack([
            cv2.resize(img, size),
            cv2.resize(binary_clean, size),
            cv2.resize(manual, size),
            cv2.resize(library, size)
        ])

        labels = [
            (f"{img_path}", 10, 30),
            ("Binary", 270, 30),
            ("Manual", 520, 30),
            ("Library", 770, 30)
        ]

        draw_labels(row, labels)
        all_rows.append(row)

    final_result = np.vstack(all_rows)
    cv2.imshow("LAB 6 - PART 2", final_result)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    while True:
        print("\n1 - Часть 1")
        print("2 - Часть 2")
        print("0 - Выход")

        choice = input("Выбор: ")
        if choice == '1':
            part_one()
        elif choice == '2':
            part_two()
        elif choice == '0':
            break
