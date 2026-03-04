"""
LoveSpace — Python-мост к C++ модулю (ctypes)
Файл: cpp_bridge.py

Использование:
    from cpp_bridge import find_free_time_cpp, calc_scores_cpp

Сборка C++:
    cd cpp_module
    g++ -O2 -shared -fPIC -o lovespace_core.so lovespace_core.cpp
"""

import ctypes
import os
import sys

# ─── ЗАГРУЗКА БИБЛИОТЕКИ ─────────────────────────────────────────────────────

def _load_lib():
    base = os.path.dirname(__file__)
    for name in ['lovespace_core.so', 'lovespace_core.dll']:
        path = os.path.join(base, 'cpp_module', name)
        if os.path.exists(path):
            return ctypes.CDLL(path)
    return None

_lib = _load_lib()

# ─── СТРУКТУРЫ ───────────────────────────────────────────────────────────────

class TimeSlotC(ctypes.Structure):
    _fields_ = [('day', ctypes.c_int),
                ('start_min', ctypes.c_int),
                ('end_min', ctypes.c_int)]

class ScoreEntryC(ctypes.Structure):
    _fields_ = [('user_id', ctypes.c_int),
                ('points', ctypes.c_int)]

class CategoryStatsC(ctypes.Structure):
    _fields_ = [('name', ctypes.c_char * 64),
                ('amount', ctypes.c_double),
                ('percent', ctypes.c_double)]

# ─── PYTHON-ОБЁРТКИ ──────────────────────────────────────────────────────────

def find_free_time_cpp(a_slots: list, b_slots: list) -> list:
    """
    a_slots, b_slots — списки dict: {day:int, start_min:int, end_min:int}
    Возвращает список свободных слотов.
    """
    if _lib is None:
        return _find_free_time_python(a_slots, b_slots)

    def to_c_array(slots):
        arr = (TimeSlotC * len(slots))()
        for i, s in enumerate(slots):
            arr[i].day = s['day']
            arr[i].start_min = s['start_min']
            arr[i].end_min = s['end_min']
        return arr

    a_arr = to_c_array(a_slots)
    b_arr = to_c_array(b_slots)
    out = (TimeSlotC * 32)()

    _lib.find_free_time.restype = ctypes.c_int
    count = _lib.find_free_time(
        a_arr, len(a_slots),
        b_arr, len(b_slots),
        out, 32
    )
    return [{'day': out[i].day, 'start_min': out[i].start_min, 'end_min': out[i].end_min}
            for i in range(count)]


def calc_scores_cpp(task_users: list, task_pts: list) -> list:
    """
    Возвращает список {'user_id': int, 'points': int}
    """
    if _lib is None or not task_users:
        return _calc_scores_python(task_users, task_pts)

    n = len(task_users)
    u_arr = (ctypes.c_int * n)(*task_users)
    p_arr = (ctypes.c_int * n)(*task_pts)
    out = (ScoreEntryC * 256)()

    _lib.calc_weekly_scores.restype = ctypes.c_int
    count = _lib.calc_weekly_scores(u_arr, p_arr, n, out, 256)
    return [{'user_id': out[i].user_id, 'points': out[i].points} for i in range(count)]


def distribute_tasks_cpp(points_list: list) -> list:
    """Распределить задачи равномерно. Возвращает список (0 или 1) для каждой задачи."""
    if _lib is None:
        return [i % 2 for i in range(len(points_list))]

    n = len(points_list)
    p_arr = (ctypes.c_int * n)(*points_list)
    out = (ctypes.c_int * n)()

    _lib.distribute_tasks.restype = ctypes.c_int
    _lib.distribute_tasks(p_arr, n, out)
    return list(out)


# ─── PYTHON FALLBACK (если .so не скомпилирован) ─────────────────────────────

def _find_free_time_python(a_slots, b_slots):
    """Pure Python fallback."""
    DAYS = 7
    DAY_START, DAY_END = 8*60, 22*60
    result = []
    for day in range(DAYS):
        busy = [(s['start_min'], s['end_min']) for s in a_slots + b_slots if s['day'] == day]
        busy.sort()
        merged = []
        for s, e in busy:
            if merged and s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append([s, e])
        cur = DAY_START
        for s, e in merged:
            if cur < s and s - cur >= 30:
                result.append({'day': day, 'start_min': cur, 'end_min': min(s, DAY_END)})
            cur = max(cur, e)
        if cur < DAY_END and DAY_END - cur >= 30:
            result.append({'day': day, 'start_min': cur, 'end_min': DAY_END})
    return result

def _calc_scores_python(users, pts):
    scores = {}
    for u, p in zip(users, pts):
        scores[u] = scores.get(u, 0) + p
    return [{'user_id': k, 'points': v} for k, v in scores.items()]


def minutes_to_hhmm(m: int) -> str:
    return f"{m//60:02d}:{m%60:02d}"
