from time import time
from datetime import datetime
from os import remove, listdir
from typing import Callable, Dict, Tuple
from os import makedirs, path


class Profiler:
    __slots__ = ()
    __is_session_started = False
    __session_data: Dict[str, Tuple[int, float]] = {}
    PROFILING_RESULT_DIRECTORY = "profiling/"

    @staticmethod
    def begin_profile_session() -> None:
        Profiler.__is_session_started = True

    @staticmethod
    def end_profile_session() -> None:
        Profiler.__is_session_started = False
        if not path.exists(Profiler.PROFILING_RESULT_DIRECTORY):
            makedirs(Profiler.PROFILING_RESULT_DIRECTORY)
        with open(Profiler.PROFILING_RESULT_DIRECTORY + f"profile_session_{str(datetime.now()).replace('.', '-').replace(':', '-')}", "w") as output_stream:
            lines = []
            for func_name, data in Profiler.__session_data.items():
                lines.append(f"{func_name} average time: {'%.3f' % (data[1] * 1000 / data[0])} ms.\n")
            output_stream.writelines(lines)

    @staticmethod
    def is_session_started() -> bool:
        return Profiler.__is_session_started

    @staticmethod
    def profile(function: Callable, *args, **kwargs):
        is_started = Profiler.is_session_started()
        start_time = 0
        if is_started:
            start_time = time()
        result = function(*args, **kwargs)
        if is_started:
            func_name = function.__qualname__
            current_data = Profiler.__session_data.get(func_name, (0, 0))
            Profiler.__session_data[func_name] = (current_data[0] + 1, current_data[1] + time() - start_time)
        return result

    @staticmethod
    def clear_log() -> None:
        for filename in listdir(Profiler.PROFILING_RESULT_DIRECTORY):
            file_path = path.join(Profiler.PROFILING_RESULT_DIRECTORY, filename)
            try:
                remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")


def profiled(func: Callable):
    def wrapper(*args, **kwargs):
        return Profiler.profile(func, *args, **kwargs)
    return wrapper
