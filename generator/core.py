import tempfile
import os
import shutil
from jina import Flow
from loguru import logger

def generate(executor: str, type: str):
    f = Flow().add(
        uses=f'jinahub+docker://{executor}',
    )

    (fp, temp_file_path) = tempfile.mkstemp()

    if type == 'k8s':
        with tempfile.TemporaryDirectory() as tmpdirname:
            f.to_k8s_yaml(tmpdirname)
            shutil.make_archive(temp_file_path, 'zip', tmpdirname)
            os.remove(temp_file_path)
        
        return (f'{temp_file_path}.zip', 'zip')

    if type == 'docker_compose':
        f.to_docker_compose_yaml(temp_file_path)

        return (temp_file_path, 'yaml')
    
    if type == 'jcloud':
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(
                f'''jtype: Flow
executors:
  - name: {executor}
    uses: jinahub+docker://{executor}'''
            )
        return (temp_file_path, 'yaml')

def clean(path: str):
    logger.info(f'Clean temp file: {path}')
    os.remove(path)
    logger.info(f'Clean successfully')