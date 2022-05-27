
import os
from soviby import helper_task


class FileGuard(object):
    def __init__(self, file_list: list):
        self._file_info_list = []
        for f in file_list:
            self._file_info_list.append(FileInfo(f))

    def check_file(self):
        is_update = False
        update_f_list = []
        for f in self._file_info_list:
            if f.is_update():
                is_update = True
                f.last_save_time = f.get_mtime()
                update_f_list.append(f)

        return (is_update, [f.path for f in update_f_list])


class FileInfo(object):
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.last_save_time = self.get_mtime()

    def get_mtime(self):
        return os.path.getmtime(self.path)

    def is_update(self):
        if not self.last_save_time:
            return False
        return self.last_save_time != self.get_mtime()


def create_file_guard(file_list: list):
    return FileGuard(file_list)
