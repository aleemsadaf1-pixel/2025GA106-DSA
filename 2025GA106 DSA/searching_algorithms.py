import time
import math


class SearchResult:
    def __init__(self, data, algorithm, time_ms, matches_found):
        self.data = data
        self.algorithm = algorithm
        self.time_ms = time_ms
        self.matches_found = matches_found


def _s(item, key):
    return str(item.get(key, "")).lower()


def _n(item, key):
    try:
        return float(item.get(key, ""))
    except (ValueError, TypeError):
        return None


def _match(item, col, val, ft):
    iv = _s(item, col)
    vl = str(val).lower()
    if ft == "exact":
        return iv == vl
    if ft == "contains":
        return vl in iv
    if ft == "starts with":
        return iv.startswith(vl)
    if ft == "ends with":
        return iv.endswith(vl)
    if ft == "not equal":
        return iv != vl
    if ft == "greater than":
        n = _n(item, col)
        try:
            v = float(val)
        except ValueError:
            return False
        return n is not None and n > v
    if ft == "less than":
        n = _n(item, col)
        try:
            v = float(val)
        except ValueError:
            return False
        return n is not None and n < v
    return False


def linear_search(data, key, value, filter_type="contains"):
    start = time.perf_counter()
    results = [item for item in data if _match(item, key, value, filter_type)]
    ms = (time.perf_counter() - start) * 1000
    return SearchResult(results, "Linear Search", ms, len(results))


def binary_search(data, key, value, filter_type="contains"):
    sd = sorted(data, key=lambda x: _s(x, key))
    vl = str(value).lower()
    start = time.perf_counter()
    results = []
    if filter_type == "exact":
        lo, hi = 0, len(sd) - 1
        found = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            mv = _s(sd[mid], key)
            if mv == vl:
                found = mid
                break
            elif mv < vl:
                lo = mid + 1
            else:
                hi = mid - 1
        if found != -1:
            results.append(sd[found])
            i = found - 1
            while i >= 0 and _s(sd[i], key) == vl:
                results.append(sd[i]); i -= 1
            i = found + 1
            while i < len(sd) and _s(sd[i], key) == vl:
                results.append(sd[i]); i += 1
    else:
        results = [item for item in sd if _match(item, key, value, filter_type)]
    ms = (time.perf_counter() - start) * 1000
    return SearchResult(results, "Binary Search", ms, len(results))


def jump_search(data, key, value, filter_type="contains"):
    sd = sorted(data, key=lambda x: _s(x, key))
    n = len(sd)
    vl = str(value).lower()
    start = time.perf_counter()
    results = []
    if filter_type == "exact" and n > 0:
        step = int(math.sqrt(n))
        prev = 0
        while prev < n and _s(sd[min(step, n)-1], key) < vl:
            prev = step
            step += int(math.sqrt(n))
            if prev >= n:
                break
        for i in range(prev, min(step, n)):
            if _s(sd[i], key) == vl:
                results.append(sd[i])
    else:
        results = [item for item in sd if _match(item, key, value, filter_type)]
    ms = (time.perf_counter() - start) * 1000
    return SearchResult(results, "Jump Search", ms, len(results))


SEARCH_ALGORITHMS = {
    "Linear Search": linear_search,
    "Binary Search": binary_search,
    "Jump Search": jump_search,
}

STRING_FILTERS = ["contains", "exact", "starts with", "ends with", "not equal"]
NUMERIC_FILTERS = ["exact", "greater than", "less than", "not equal"]


def multi_column_search(data, filters, combine="AND"):
    start = time.perf_counter()
    results = []
    for item in data:
        verdicts = []
        for f in filters:
            m = _match(item, f["column"], f["value"], f["filter_type"])
            if f.get("negate", False):
                m = not m
            verdicts.append(m)
        if combine == "AND" and all(verdicts):
            results.append(item)
        elif combine == "OR" and any(verdicts):
            results.append(item)
    ms = (time.perf_counter() - start) * 1000
    return SearchResult(results, f"Multi-Column ({combine})", ms, len(results))
