import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (
    BASE_DIR,
    DATETIME_FORMAT,
    RESULTS_DIR,
    FILE_MODE,
    PRETTY_MODE,
)


FILE_SAVED_FORMAT = 'Файл с результатами был сохранён: {file_path}'


def file_output(results, cli_args):
    results_dir = BASE_DIR / RESULTS_DIR
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    datetime = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{datetime}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding='UTF-8') as file:
        writer = csv.writer(file, dialect=csv.unix_dialect)
        writer.writerows(results)
    logging.info(FILE_SAVED_FORMAT.format(file_path=file_path))


def pretty_output(results, *args):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def default_output(results, *args):
    for row in results:
        print(*row)


OUTPUT_TO_FUNCTIONS = {
    PRETTY_MODE: pretty_output,
    FILE_MODE: file_output,
}


def control_output(results, cli_args):
    output = cli_args.output
    OUTPUT_TO_FUNCTIONS.get(output, default_output)(results, cli_args)
