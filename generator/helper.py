
def to_jcloud_yaml(output_path: str, executor: str,protocol: str):
    import yaml
    document = f'''
    jtype: Flow
    with:
        protocol: {protocol}
    executors:
      - name: { executor if executor.isidentifier() else fix_executor_name(executor) }
        uses: jinahub+docker://{executor}'''
    # for safe, don't trust any params
    jsonYaml = yaml.safe_load(document);
    with open(output_path, 'w+', encoding='utf-8') as fd:
        yaml.dump(jsonYaml, fd, sort_keys=False)
    print(f'[b]{output_path}[/b]. You can use it by running')

def fix_executor_name(executor: str):
    import re
    temp_executor_name = re.sub(r'\W','_',executor);
    finally_executor_name =  f'_{temp_executor_name}' if re.match(r'^\d',temp_executor_name) else temp_executor_name
    return finally_executor_name if finally_executor_name.isidentifier() else 'default_executor_name'