import time

def calc_speed(current, total, start_time):

    elapsed = time.time() - start_time + 0.1
    speed = current / elapsed

    percent = int(current * 100 / total)

    eta = (total - current) / speed if speed > 0 else 0

    return percent, speed, int(eta)
