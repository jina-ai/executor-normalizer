def to_j_cloud_yaml( output_path: str, executor: str,protocol: str):
    import yaml
    document = f'''
    jtype: Flow
    with:
        protocol: {protocol}
    executors:
      - name: {executor.replace('/','_').replace('-','_')}
        uses: jinahub+docker://{executor}'''
    # for safe, don't trust any params
    jsonYaml = yaml.safe_load(document);
    with open(output_path, 'w+', encoding='utf-8') as fs:
        yaml.dump(jsonYaml, fs,sort_keys=False)
    print(f'[b]{output_path}[/b]. You can use it by running')