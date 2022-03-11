import time
import os

import yaml
from kubernetes import client, config
from jina import Flow
from kubernetes.client import ApiException
from .constants import SANDBOX_DOMAIN

try:
    config.load_kube_config(os.environ.get('KUBECONFIG'))
except Exception as ex:
    print('Error when loading kube config. Sandbox is not avaliable.')
    print(str(ex))

k8s_client = client.ApiClient()

v1_api = client.CoreV1Api(api_client=k8s_client)
networking_api = client.NetworkingV1Api(api_client=k8s_client)


def delete_flow(namespace):
    print('delete namespace for: ', namespace)
    try:
        v1_api.delete_namespace(namespace)
    except ApiException as e:
        if e.status == 404:
            print('Namespace does not exist. No need to delete it')
        else:
            raise Exception('Error during namespace deletion', e)
    wait_for_namespace_to_be_deleted(namespace)


def create_ingress(name, namespace):
    for service_name, purpose, port in [('gateway', 'flow', '8080'), (name, 'pod', '8081')]:
        print(f'create ingress on {service_name} for {purpose}')
        ingress_name = f'{name}-{purpose}'
        ingress_yaml = yaml.safe_load(
            f'''
apiVersion: networking.k8s.io/v1beta1\n
kind: Ingress\n
metadata:\n
  name: {ingress_name}\n
  namespace: {namespace}\n
  annotations:\n
    kubernetes.io/ingress.class: nginx\n
    nginx.ingress.kubernetes.io/rewrite-target: /$1\n
spec:\n
  rules:\n
  - http:\n
      paths:\n
      - path: /sandbox/{purpose}/{name}/(.+)\n
        pathType: Prefix\n
        backend:\n
          serviceName: {service_name}\n
          servicePort: {port}\n
        '''
        )
        networking_api.create_namespaced_ingress(namespace, ingress_yaml)
        wait_for_ingress_to_start(ingress_name, namespace)


def wait_for_namespace_to_be_deleted(namespace):
    for i in range(100):
        namespaces = v1_api.list_namespace()
        namespaces = [item.metadata.name for item in namespaces.items]
        if namespace not in namespaces:
            print('Namespace is not there. Ready for deployment')
            return
        print(f'wait for namespace {namespace} to be deleted')
        time.sleep(5)
    raise Exception(f'Namespace {namespace} must be removed before deployment')


def wait_for_ingress_to_start(ingress_name, namespace):
    for i in range(100):
        resp = networking_api.read_namespaced_ingress_status(ingress_name, namespace)
        if resp.status.load_balancer.ingress:
            print(f'Ingress set up successfully for {ingress_name} in namespace {namespace}')
            return
        time.sleep(1)
    raise Exception(f'Ingress {ingress_name} in namespace {namespace} can not reach service')


def deploy_flow(executor, name, namespace, endpoints, replicas):
    print('deploy flow for: ', executor)
    f = Flow(
        name=namespace,
        port_expose=8080,
        infrastructure='K8S',
        protocol='http',
        replicas=replicas,
    ).add(
        uses=f'jinahub+docker://{executor}',
        name=name
    )
    for endpoint in endpoints:
        f.expose_endpoint(f'/{endpoint}')
    f.start()
    print('create ingress for: ', executor)
    create_ingress(name, namespace)


def deploy(executor, endpoints, replicas):
    start_time = time.time()

    # name for both deployment and service
    name = executor.lower().replace('_', '-')
    namespace = f'sandbox-{name}'

    delete_flow(namespace)
    deploy_flow(executor, name, namespace, endpoints, replicas)
    print(
        f'Deployment of {executor} successful [endpoints: {endpoints}, replicas{replicas}]. Cost {time.time() - start_time} seconds totally')

    return {
        'flow_url': f'http://{SANDBOX_DOMAIN}/sandbox/flow/{name}',
        'pod_url': f'http://{SANDBOX_DOMAIN}/sandbox/pod/{name}',
    }