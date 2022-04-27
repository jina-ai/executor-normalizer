from jina import Flow

def generate(executor: str, type: str):
    f = Flow().add(
        uses=f'jinahub+docker://{executor}',
    )

    # if type == 'k8s':
    #     f.to_k8s_yaml()
    # elif type == 'docker_compose':
    #     f.to_docker_compose_yaml()
    # elif type == 'jcloud':
    #     pass

    return 'test'
