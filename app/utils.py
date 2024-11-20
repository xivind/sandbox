#!/usr/bin/env python3

import json

def read_json_file(path):
    """Function to read json file"""
    with open(path, 'r', encoding='utf-8') as file:
        dictionary = json.load(file)
    return dictionary