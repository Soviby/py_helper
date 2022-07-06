import _thread
import time


def delay(ms, func):
    result = {}
    is_stop = False

    def stop():
        nonlocal is_stop
        is_stop = True
    result['stop_func'] = stop

    def _handle():
        time.sleep(ms / 1000)
        if is_stop:
            return
        func()
    _thread.start_new_thread(_handle, ())
    return result


def loop(ms, func) -> dict:
    result = {}
    is_stop = False

    def stop():
        nonlocal is_stop
        is_stop = True
    result['stop_func'] = stop

    def _handle():
        while True:
            time.sleep(ms / 1000)
            if is_stop:
                break
            func()
            
    _thread.start_new_thread(_handle, ())
    return result


def wait_until(until_func, func):
    result = {}
    is_stop = False

    def stop():
        nonlocal is_stop
        is_stop = True
    result['stop_func'] = stop

    def _handle():
        while True:
            if is_stop or until_func():
                func()
                break
            time.sleep(0.05)
            

    _thread.start_new_thread(_handle, ())
    return result
