import sys, os

sys.path.insert(0, r'plugins\Googler\Lib\site-packages')
# for module in os.listdir(r'plugins\Googler\Lib\site-packages'):
#     exec(f"import {module}")

import requests


def start():
    print("Googler plugin is running")

def google():
    return "Hello"