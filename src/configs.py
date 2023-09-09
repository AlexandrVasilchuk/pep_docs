import logging

import argparse
from logging.handlers import RotatingFileHandler

from constants import BASE_DIR, LOG_FROMAT, DT_FORMAT


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
        choices=('pretty', 'file'),
        help='Дополнительные способы вывода данных',
    )
    return parser


def configure_logging():
    log_dir = BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'parser.log'
    rotation_handler = RotatingFileHandler(
        log_file, maxBytes=10**6, backupCount=5
    )
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FROMAT,
        datefmt=DT_FORMAT,
        handlers=(rotation_handler, logging.StreamHandler()),
    )
