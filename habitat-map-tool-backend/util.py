import time

start = time.time()

def get_elapsed_time():
    global start
    elapsed = time.time() - start
    start = time.time()
    return " - "+str(round(elapsed,2)) + "s"

