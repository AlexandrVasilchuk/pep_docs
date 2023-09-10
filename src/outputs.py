import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT


FILE_SAVED_FORMAT = 'Файл с результатами был сохранён: {file_path}'


def file_output(results, cli_args):
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    file_name = f'{parser_mode}_{dt.datetime.now().strftime(DATETIME_FORMAT)}.csv'
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


OUTPUT_TO_FUNCTION = {'pretty': pretty_output, 'file': file_output}


def control_output(results, cli_args):
    output = cli_args.output
    OUTPUT_TO_FUNCTION.get(output, default_output)(results, cli_args)


def default_output(results, *args):
    for row in results:
        print(*row)
