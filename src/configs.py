import logging
from logging.handlers import RotatingFileHandler

import argparse

from constants import DT_FORMAT, LOG_DIR, LOG_FROMAT
from outputs import OUTPUT_TO_FUNCTION


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode', choices=available_modes, help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c', '--clear-cache', action='store_true', help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=tuple(OUTPUT_TO_FUNCTION.keys()),
        help='Дополнительные способы вывода данных',
    )
    return parser


def configure_logging(filename='parser.log'):
    rotation_handler = RotatingFileHandler(
        LOG_DIR / filename, maxBytes=10**6, backupCount=5
    )
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FROMAT,
        datefmt=DT_FORMAT,
        handlers=(rotation_handler, logging.StreamHandler()),
    )
