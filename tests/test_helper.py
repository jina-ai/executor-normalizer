from pathlib import Path
from normalizer import helper
from generator import helper as generator_helper
import tempfile
from generator.core import clean as clean_yaml

cur_dir = Path(__file__).parent


def test_choose_jina_version(mocker):
    mocker.patch('normalizer.helper.get_jina_latest_version', return_value='2.0.0rc10')

    assert helper.choose_jina_version('2.0.0rc11') == '2.0.0rc10'
    assert helper.choose_jina_version('2.0.0rc9') == '2.0.0rc9'
    assert helper.choose_jina_version('master') == 'master'


def test_convert_from_path():
    assert helper.convert_from_to_path('..deps', base_dir=cur_dir / 'cases/nested_3/executors')
    assert helper.convert_from_to_path('deps', base_dir= cur_dir / 'cases/nested_3')

def test_to_jcloud_yaml():
    (fp, temp_file_path) = tempfile.mkstemp()
    assert generator_helper.to_jcloud_yaml(temp_file_path, '^_123!.executor/v1.2.3', 'grpc')
    clean_yaml(temp_file_path) 

def test_fix_executor_name():
    assert generator_helper.fix_executor_name('*^__4eadqe7213/p234986^&*.^%#$@$#%*&@~xector/v1.2.3') == 'executor____4eadqe7213_p234986________________xector_v1_2_3'