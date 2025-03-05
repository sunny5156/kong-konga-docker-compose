
import requests
import json
from typing import Dict, List

# 配置旧版和新版Kong Admin API地址

# OLD_KONG_ADMIN = "http://10.100.0.239:8839"
# NEW_KONG_ADMIN = "http://10.100.1.239:8011"


# 禁用SSL验证（如果有HTTPS且证书不受信任）
SESSION = requests.Session()
SESSION.verify = False

def fetch_all_entities(admin_url: str, entity_path: str) -> List[Dict]:
    """从Kong Admin API获取所有分页数据"""
    entities = []
    next_url = f"{admin_url}/{entity_path}"

    # print(next_url)

    while next_url:
        response = SESSION.get(next_url)
        # print(response.text)
        response.raise_for_status()
        data = response.json()
        entities.extend(data["data"])

        next_path = data.get("next")
        if next_path:
            next_url = admin_url+next_path  # 正确拼接绝对URL
        else:
            next_url = None  # 没有下一页时退出循环

    return entities

def migrate_services(old_services: List[Dict]) -> Dict[str, str]:
    """迁移Services并返回旧ID到新ID的映射"""
    id_mapping = {}
    for service in old_services:
        # print(service)
        old_id = service["id"]
        # 移除旧版本特定字段或转换
        new_service = {
            "name": service["name"],
            "path": service["path"],
            "host": service.get("host"),
            "port": service.get("port", 80),
            # 其他字段按需添加
            "created_at": service["created_at"],
            "tags": service["tags"],
            
        }

        # 如果存在url字段则覆盖
        if "url" in service:
            new_service["url"] = service["url"]
        else:
            # 自动拼接URL格式
            new_service["url"] = f"{service['protocol']}://{service['host']}:{service['port']}{service['path']}"

        # 创建新Service
        resp = SESSION.post(f"{NEW_KONG_ADMIN}/services", data=new_service)
        if resp.status_code == 409:
            print(f"Service {service['name']} 已存在，跳过")
            # 获取现有ID
            existing = SESSION.get(f"{NEW_KONG_ADMIN}/services/{service['name']}").json()
            id_mapping[old_id] = existing["id"]
            continue
        resp.raise_for_status()
        new_service = resp.json()
        id_mapping[old_id] = new_service["id"]
    return id_mapping

def migrate_routes(old_routes: List[Dict], service_id_mapping: Dict[str, str]) -> Dict[str, str]:
    """迁移Routes并返回旧ID到新ID的映射"""
    id_mapping = {}
    for route in old_routes:
        old_id = route["id"]
        # 转换字段，例如处理strip_path到path_handling
        new_route = {
            "name": route.get("name"),
            "paths": route.get("paths", []),
            "methods": route.get("methods"),
            "service": {"id": service_id_mapping[route["service"]["id"]]},
            "path_handling": "v1",  # 根据Kong 3.x的配置调整
            "created_at": route["created_at"],
            "tags": route["tags"],
            "hosts": route["hosts"],
            "protocols": route["protocols"],
            "headers": route["headers"],

        }
        # 移除旧版本无效字段
        new_route.pop("strip_path", None)
        # 创建新Route
        resp = SESSION.post(f"{NEW_KONG_ADMIN}/routes", json=new_route)
        if resp.status_code == 409:
            print(f"Route {route.get('name')} 已存在，跳过")
            # 获取现有ID（假设通过名称唯一）
            existing = SESSION.get(f"{NEW_KONG_ADMIN}/routes/{route['name']}").json()
            id_mapping[old_id] = existing["id"]
            continue
        resp.raise_for_status()
        new_route = resp.json()
        id_mapping[old_id] = new_route["id"]
    return id_mapping

def migrate_plugins(old_plugins: List[Dict], service_id_map: Dict, route_id_map: Dict):
    """迁移插件，关联到新的Service/Route ID"""
    for plugin in old_plugins:
        # 确定关联的实体类型（service或route）
        config = plugin["config"]
        old_plugin_service = plugin['service']
        old_plugin_route = plugin['route']
        if old_plugin_service is not None:
            old_plugin_service_id = old_plugin_service['id']
        else:
            old_plugin_service_id = None

        if old_plugin_route is not None:
            old_plugin_route_id = old_plugin_route['id']
        else:
            old_plugin_route_id = None
        
        if old_plugin_service_id is not None:
            new_service_id = service_id_map.get(old_plugin_service_id)
            if not new_service_id:
                print(f"无法找到Service {new_service_id} 的新ID，跳过插件")
                continue
            plugin_body = {
                "name": plugin["name"],
                "service": {"id": new_service_id},
                "config": config,
                "enabled": True,  # Kong 3.x可能需要显式启用
                "created_at": plugin["created_at"],
                "tags": plugin["tags"],
            }
        # elif plugin.get("route_id"):
        elif old_plugin_route_id is not None:
            new_route_id = route_id_map.get(old_plugin_route_id)
            if not new_route_id:
                print(f"无法找到Route {old_plugin_route_id} 的新ID，跳过插件")
                continue
            plugin_body = {
                "name": plugin["name"],
                "route": {"id": new_route_id},
                "config": config,
                "enabled": True,
                "created_at": plugin["created_at"],
                "tags": plugin["tags"],
            }
        else:
            print("插件未关联Service或Route，跳过")
            continue

        # 检查插件是否兼容新版本
        resp = SESSION.post(f"{NEW_KONG_ADMIN}/plugins", json=plugin_body)
        if resp.status_code == 409:
            print(f"Plugin {plugin['name']} 已存在，跳过")
            continue
        if resp.status_code == 400:
            print(f"插件 {plugin['name']} 配置不兼容: {resp.text}")
        else:
            resp.raise_for_status()

def migrate_upstreams(old_upstreams: List[Dict]) -> Dict[str, str]:
    """迁移Upstreams并返回ID映射"""
    id_mapping = {}
    for upstream in old_upstreams:
        # 检查是否已存在
        check_resp = SESSION.get(
            f"{NEW_KONG_ADMIN}/upstreams/{upstream['name']}",
            params={"name": upstream["name"]}
        )
        if check_resp.status_code == 200:
            print(f"Upstream {upstream['name']} 已存在，跳过创建")
            id_mapping[upstream["id"]] = check_resp.json()["id"]
            continue

        # 构建新的Upstream配置
        new_upstream = {
            "name": upstream["name"],
            "algorithm": upstream.get("algorithm", "round-robin"),
            "hash_on": upstream.get("hash_on", "none"),
            "hash_fallback": upstream.get("hash_fallback", "none"),
            "healthchecks": upstream.get("healthchecks", {}),
            "slots": upstream.get("slots", 10000),
            "created_at": upstream["created_at"],
            "tags": upstream["tags"],
        }
        
        try:
            resp = SESSION.post(f"{NEW_KONG_ADMIN}/upstreams", json=new_upstream)
            if resp.status_code == 409:
                existing = SESSION.get(f"{NEW_KONG_ADMIN}/upstreams/{upstream['name']}").json()
                id_mapping[upstream["id"]] = existing["id"]
                print(f"Upstream {upstream['name']} 冲突，使用现有实例")
                continue
            resp.raise_for_status()
            id_mapping[upstream["id"]] = resp.json()["id"]
        except Exception as e:
            print(f"创建Upstream {upstream['name']} 失败: {str(e)}")
            continue
    
    return id_mapping

def migrate_targets(old_upstreams: List[Dict], upstream_id_mapping: Dict[str, str]):
    """迁移Targets"""
    for upstream in old_upstreams:
        new_upstream_id = upstream_id_mapping.get(upstream["id"])
        if not new_upstream_id:
            continue
        
        # 获取旧Targets
        targets = fetch_all_entities(
            OLD_KONG_ADMIN,
            f"upstreams/{upstream['id']}/targets"
        )
        
        for target in targets:
            # 检查是否已存在
            # check_resp = SESSION.get(
            #     f"{NEW_KONG_ADMIN}/upstreams/{new_upstream_id}/targets",
            #     params={"target": target["target"]}
            # )
            # if check_resp.status_code == 200 and len(check_resp.json()["data"]) > 0:
            #     print(f"Target {target['target']} 已存在，跳过")
            #     continue

            # 创建新Target
            new_target = {
                "target": target["target"],
                "weight": target.get("weight", 100),
                "tags": target.get("tags", []),
                "created_at": target["created_at"],
            }
            
            try:
                resp = SESSION.post(
                    f"{NEW_KONG_ADMIN}/upstreams/{new_upstream_id}/targets",
                    json=new_target
                )
                if resp.status_code == 409:
                    print(f"Target {target['target']} 冲突，可能已存在")
                    continue
                resp.raise_for_status()
            except Exception as e:
                print(f"创建Target {target['target']} 失败: {str(e)}")

def main():
    # 新增Upstream迁移流程
    print("导出Upstreams...")
    old_upstreams = fetch_all_entities(OLD_KONG_ADMIN, "upstreams")
    
    print("迁移Upstreams...")
    upstream_id_mapping = migrate_upstreams(old_upstreams)
    
    print("迁移Targets...")
    migrate_targets(old_upstreams, upstream_id_mapping)

    # 导出旧数据
    print("导出Services...")
    old_services = fetch_all_entities(OLD_KONG_ADMIN, "services")
    print("导出Routes...")
    old_routes = fetch_all_entities(OLD_KONG_ADMIN, "routes")
    print("导出Plugins...")
    old_plugins = fetch_all_entities(OLD_KONG_ADMIN, "plugins")

    # 迁移Services
    print("迁移Services...")
    service_id_mapping = migrate_services(old_services)

    # 迁移Routes
    print("迁移Routes...")
    route_id_mapping = migrate_routes(old_routes, service_id_mapping)

    # 迁移Plugins
    print("迁移Plugins...")
    migrate_plugins(old_plugins, service_id_mapping, route_id_mapping)

    print("迁移完成")

if __name__ == "__main__":
    main()
