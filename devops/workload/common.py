import json
from libs.utils.redis_com import rd
# pods_api 接口
from devops import k8s_tools
from kubernetes import client

from devops.settings import TOKEN
from libs.utils import db


def pods_api(auth_type, token, namespace):
    """获取pods"""
    # 接口缓存10分钟
    redis_key = f"pods_api-{namespace}"
    k8s = rd.k8s.get(redis_key)
    if k8s:
        return json.loads(k8s)
    k8s_tools.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    data = []
    try:
        for po in core_api.list_namespaced_pod(namespace).items:
            name = po.metadata.name
            namespace = po.metadata.namespace
            labels = po.metadata.labels
            pod_ip = po.status.pod_ip
            containers = []  # [{},{},{}]
            status = "None"
            # 只为None说明Pod没有创建（不能调度或者正在下载镜像）
            if po.status.container_statuses is None:
                status = po.status.conditions[-1].reason
            else:
                for c in po.status.container_statuses:
                    c_name = c.name
                    c_image = c.image
                    # 获取重启次数
                    restart_count = c.restart_count
                    # 获取容器状态
                    c_status = "None"
                    if c.ready is True:
                        c_status = "Running"
                    elif c.ready is False:
                        if c.state.waiting is not None:
                            c_status = c.state.waiting.reason
                        elif c.state.terminated is not None:
                            c_status = c.state.terminated.reason
                        elif c.state.last_state.terminated is not None:
                            c_status = c.last_state.terminated.reason

                    c = {'c_name': c_name, 'c_image': c_image, 'restart_count': restart_count, 'c_status': c_status}
                    containers.append(c)
            create_time = k8s_tools.dt_format(po.metadata.creation_timestamp)
            po = {"name": name, "namespace": namespace, "pod_ip": pod_ip,
                  "labels": labels, "containers": containers, "status": status,
                  "create_time": create_time}
            data.append(po)
    except Exception as e:
        print(e)
    return data


def get_link_url(sid):
    """获取做题连接"""
    sub = db.web.subjects.get(id=sid)
    if not sub:
        return False, '学科不存在'
    namespace = sub.namespace
    pods = pods_api('token', TOKEN, namespace)
    link_url = ''
    for pod in pods:
        pod_name = pod['name']
        containers = pod['containers'][0]['c_name']
        redis_key = f"pod_status-{pod_name}"
        pod_status = rd.k8s.get(redis_key)
        if not pod_status:  # 未使用
            link_url = f"/k8workload/terminal_web/?namespace={namespace}" \
                       f"&pod_name={pod_name}" \
                       f"&containers={containers}"
            break
    if not link_url:
        return False, '暂无可用pod'
    return True, link_url


