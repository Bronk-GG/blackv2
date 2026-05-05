import random
import os


import sys

def getRandomUserAgent(config):
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    path = os.path.join(base_dir, "data", "useragents.txt")
    userAgents = open(path).read().splitlines()
    userAgent = random.choice(userAgents)
    if config.verbose:
        config.console.print(f':id: Selected random User-Agent "{userAgent}"')
    return userAgent
