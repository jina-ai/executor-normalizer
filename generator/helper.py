import re
import uuid
import yaml

def to_jcloud_yaml(output_path: str, executor: str,protocol: str):
    document = f'''
    jtype: Flow
    with:
        protocol: {protocol}
    executors:
      - name: { executor if check_executor_name(executor) else fix_executor_name(executor) }
        uses: jinahub+docker://{executor}'''
    # for safe, don't trust any params
    jsonYaml = yaml.safe_load(document)
    with open(output_path, 'w+', encoding='utf-8') as fd:
        yaml.dump(jsonYaml, fd, sort_keys=False)
    print(f'[b]{output_path}[/b]. You can use it by running')
    return True

def check_executor_name(executor):
    return is_python_variable_name(executor) and not is_start_with_name(executor)

def is_python_variable_name(executor: str):
    return executor.isidentifier()

def is_start_with_name(executor: str):
    return True if re.match(r'^_+\d',executor) is not None else False

def fix_executor_name(executor: str):
    python_variable_name = executor if is_python_variable_name(executor) else re.sub(r'\W','_',executor)
    extends_executor_name = f'executor{python_variable_name}' if is_start_with_name(python_variable_name) else python_variable_name
    finally_executor_name = extends_executor_name if check_executor_name(extends_executor_name) else f'default_executor_name_{str(uuid.uuid4())[0:7]}'
    return finally_executor_name if check_executor_name(finally_executor_name) else 'default_executor_name'