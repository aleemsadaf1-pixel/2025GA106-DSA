import time
import copy
import random


class SortResult:
    def __init__(self, data, comparisons, swaps, time_ms, algorithm, time_complexity, stable):
        self.data = data
        self.comparisons = comparisons
        self.swaps = swaps
        self.time_ms = time_ms
        self.algorithm = algorithm
        self.time_complexity = time_complexity
        self.stable = stable


def _val(item, key):
    v = item.get(key, "")
    if isinstance(v, (int, float)):
        return v
    try:
        return float(v)
    except (ValueError, TypeError):
        return str(v).lower()


def bubble_sort(data, key, reverse=False):
    arr = copy.deepcopy(data)
    n = len(arr)
    comps = swaps = 0
    start = time.perf_counter()
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            comps += 1
            if (_val(arr[j], key) > _val(arr[j+1], key)) != reverse:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swaps += 1
                swapped = True
        if not swapped:
            break
    ms = (time.perf_counter() - start) * 1000
    return SortResult(arr, comps, swaps, ms, "Bubble Sort", "O(n²)", True)


def selection_sort(data, key, reverse=False):
    arr = copy.deepcopy(data)
    n = len(arr)
    comps = swaps = 0
    start = time.perf_counter()
    for i in range(n - 1):
        best = i
        for j in range(i + 1, n):
            comps += 1
            if (_val(arr[j], key) < _val(arr[best], key)) != reverse:
                best = j
        if best != i:
            arr[i], arr[best] = arr[best], arr[i]
            swaps += 1
    ms = (time.perf_counter() - start) * 1000
    return SortResult(arr, comps, swaps, ms, "Selection Sort", "O(n²)", False)


def insertion_sort(data, key, reverse=False):
    arr = copy.deepcopy(data)
    n = len(arr)
    comps = swaps = 0
    start = time.perf_counter()
    for i in range(1, n):
        ki = arr[i]
        j = i - 1
        while j >= 0:
            comps += 1
            if (_val(arr[j], key) > _val(ki, key)) != reverse:
                arr[j+1] = arr[j]
                swaps += 1
                j -= 1
            else:
                break
        arr[j+1] = ki
    ms = (time.perf_counter() - start) * 1000
    return SortResult(arr, comps, swaps, ms, "Insertion Sort", "O(n²)", True)


def merge_sort(data, key, reverse=False):
    comps = [0]
    swaps = [0]

    def merge(arr, l, m, r):
        L, R = arr[l:m+1], arr[m+1:r+1]
        i = j = 0
        k = l
        while i < len(L) and j < len(R):
            comps[0] += 1
            if (_val(L[i], key) <= _val(R[j], key)) != reverse:
                arr[k] = L[i]; i += 1
            else:
                arr[k] = R[j]; j += 1
            swaps[0] += 1; k += 1
        while i < len(L):
            arr[k] = L[i]; i += 1; k += 1
        while j < len(R):
            arr[k] = R[j]; j += 1; k += 1

    def sort(arr, l, r):
        if l < r:
            m = (l + r) // 2
            sort(arr, l, m)
            sort(arr, m+1, r)
            merge(arr, l, m, r)

    arr = copy.deepcopy(data)
    start = time.perf_counter()
    if len(arr) > 1:
        sort(arr, 0, len(arr)-1)
    ms = (time.perf_counter() - start) * 1000
    return SortResult(arr, comps[0], swaps[0], ms, "Merge Sort", "O(n log n)", True)


def quick_sort(data, key, reverse=False):
    comps = [0]
    swaps = [0]

    def partition(arr, lo, hi):
        pi = random.randint(lo, hi)
        arr[pi], arr[hi] = arr[hi], arr[pi]
        swaps[0] += 1
        pivot = _val(arr[hi], key)
        i = lo - 1
        for j in range(lo, hi):
            comps[0] += 1
            if (_val(arr[j], key) <= pivot) != reverse:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                swaps[0] += 1
        arr[i+1], arr[hi] = arr[hi], arr[i+1]
        swaps[0] += 1
        return i + 1

    def sort(arr, lo, hi):
        if lo < hi:
            p = partition(arr, lo, hi)
            sort(arr, lo, p-1)
            sort(arr, p+1, hi)

    import sys
    arr = copy.deepcopy(data)
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, len(arr) + 500))
    start = time.perf_counter()
    if len(arr) > 1:
        sort(arr, 0, len(arr)-1)
    ms = (time.perf_counter() - start) * 1000
    sys.setrecursionlimit(old)
    return SortResult(arr, comps[0], swaps[0], ms, "Quick Sort", "O(n log n)", False)


def heap_sort(data, key, reverse=False):
    comps = [0]
    swaps = [0]

    def heapify(arr, n, i):
        largest = i
        l, r = 2*i+1, 2*i+2
        if l < n:
            comps[0] += 1
            if (_val(arr[l], key) > _val(arr[largest], key)) != reverse:
                largest = l
        if r < n:
            comps[0] += 1
            if (_val(arr[r], key) > _val(arr[largest], key)) != reverse:
                largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            swaps[0] += 1
            heapify(arr, n, largest)

    import sys
    arr = copy.deepcopy(data)
    n = len(arr)
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, n + 500))
    start = time.perf_counter()
    for i in range(n//2-1, -1, -1):
        heapify(arr, n, i)
    for i in range(n-1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        swaps[0] += 1
        heapify(arr, i, 0)
    ms = (time.perf_counter() - start) * 1000
    sys.setrecursionlimit(old)
    return SortResult(arr, comps[0], swaps[0], ms, "Heap Sort", "O(n log n)", False)


def shell_sort(data, key, reverse=False):
    arr = copy.deepcopy(data)
    n = len(arr)
    comps = swaps = 0
    start = time.perf_counter()
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            while j >= gap:
                comps += 1
                if (_val(arr[j-gap], key) > _val(temp, key)) != reverse:
                    arr[j] = arr[j-gap]
                    swaps += 1
                    j -= gap
                else:
                    break
            arr[j] = temp
        gap //= 2
    ms = (time.perf_counter() - start) * 1000
    return SortResult(arr, comps, swaps, ms, "Shell Sort", "O(n log²n)", False)


def comb_sort(data, key, reverse=False):
    arr = copy.deepcopy(data)
    n = len(arr)
    comps = swaps = 0
    start = time.perf_counter()
    gap = n
    done = False
    while not done:
        gap = max(1, int(gap / 1.3))
        if gap == 1:
            done = True
        for i in range(n - gap):
            comps += 1
            if (_val(arr[i], key) > _val(arr[i+gap], key)) != reverse:
                arr[i], arr[i+gap] = arr[i+gap], arr[i]
                swaps += 1
                done = False
    ms = (time.perf_counter() - start) * 1000
    return SortResult(arr, comps, swaps, ms, "Comb Sort", "O(n²/2^p)", False)


ALGORITHMS = {
    "Bubble Sort": bubble_sort,
    "Selection Sort": selection_sort,
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort,
    "Heap Sort": heap_sort,
    "Shell Sort": shell_sort,
    "Comb Sort": comb_sort,
}
