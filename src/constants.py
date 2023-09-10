from pathlib import Path
from urllib.parse import urljoin


BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR = BASE_DIR / 'downloads'
DOWNLOADS_DIR.mkdir(exist_ok=True)
RESULTS_DIR = BASE_DIR / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

MAIN_DOC_URL = 'https://docs.python.org/3/'
WHATS_NEW_URL = urljoin(MAIN_DOC_URL, 'whatsnew/')
DOWNLOADS_URL = urljoin(MAIN_DOC_URL, 'download.html')
PEP_TABLE_URL = 'https://peps.python.org/'

DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
LOG_FROMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
