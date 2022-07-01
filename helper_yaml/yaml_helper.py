from soviby import helper
import soviby.LRU as LRU
import os
import yaml
import re


class YamlData(object):
    # stream
    def __init__(self, path: str, **kwargs):
        # 解析：
        # 读取文本
        # 逐行解析，
        # 直到，该行内容为非空和非注释,获得 继承的YamlData 和模板的YamlData
        # 将后面内容，作为主体进行yaml解析，然后进行继承，再进行模板替换，替换用的map需要将继承的YamlData的模板一起合并，还有将自己的文本作用域模板也要一起合并，在进行模板替换
        # 缓存YamlData对象，包含的字段 继承的YamlData 和模板的YamlData，原始map，替换后的map

        self.ref_map = {}
        self.extend_list = []
        self.template_list = []
        self.original_data_map = {}  # 没用模板替换前的数据
        self.data_map = {}  # 用模板替换后的数据

        encoding = kwargs.get('encoding')
        self.encoding = encoding
        self.path = path
        self.load(path, encoding)

    def get_abspath(self, path):
        if os.path.isabs(path):
            return path
        dirname = os.path.dirname(self.path)
        return os.path.abspath(os.path.join(dirname, path))

    def load(self, path,  encoding: str = 'utf-8'):
        with open(path,  encoding=encoding) as f:
            lines = f.readlines()
            # 解析头部
            next_line_index = 0
            for line in lines:
                line = line.strip()
                if (not line.startswith('#')) and line != '':
                    break
                if line.startswith('#'):
                    line = line[1:]
                line = line.strip()
                next_line_index = next_line_index+1
                line, _ = template_replace(line, self.ref_map)
                # 进行模板替换
                for k, v in line_func_map.items():
                    matchObj = re.search(k, line)
                    if matchObj:
                        v(self, matchObj)
                        break

            # 解析yaml
            yaml_lines = lines[next_line_index:]
            yaml_data = yaml.load('\n'.join(yaml_lines), Loader=yaml.CLoader)
            # 继承
            self.original_data_map = yaml_data if yaml_data else {}
            for extend in self.extend_list:
                self.original_data_map = map_update(
                    extend.original_data_map, self.original_data_map)
            # 递归每一个value,进行模板替换
            if not self.ref_map:
                self.data_map = self.original_data_map
            else:
                self.data_map, _ = template_replace(
                    self.original_data_map, self.ref_map)


line_func_map = {
    r'^@extend\((.+)\)': lambda self, matchObj: line_extend_func(self, matchObj),
    r'^@template\((.+)\)': lambda self, matchObj: line_template_func(self, matchObj),
    r'^@([^:]+?):(.+)': lambda self, matchObj: line_ref_func(self, matchObj),
}


def _create_func(path, kwargs):
    return YamlData(path, encoding=kwargs.get('encoding'))


def _destroy_func(yaml_data):
    pass


LRU_mgr = LRU.LRUManager(create_func=_create_func, destroy_func=_destroy_func)


def line_extend_func(self, matchObj):
    path = matchObj.group(1)
    if path:
        path = path.strip()
        path = self.get_abspath(path)
        extend = LRU_mgr.get_item(path, encoding=self.encoding)
        self.extend_list.append(extend)
        self.ref_map = map_update(self.ref_map, extend.ref_map)


def line_template_func(self, matchObj):
    path = matchObj.group(1)
    if path:
        path = path.strip()
        path = self.get_abspath(path)
        template = LRU_mgr.get_item(path, encoding=self.encoding)
        self.template_list.append(template)
        self.ref_map = map_update(self.ref_map,  template.data_map)


def line_ref_func(self, matchObj):
    key = matchObj.group(1)
    value = matchObj.group(2)
    if key and value:
        self.ref_map = map_update(self.ref_map,  {key.strip(): value.strip()})


def get_enumerate(map: dict | list):
    if type(map) == dict:
        return map.items()
    elif type(map) == list:
        return enumerate(map)


def enable_enumerate(map: any):
    return type(map) == dict or type(map) == list


# updated_map 被更新的字典
# use_map 用来更新的字典
def map_update(updated_map: dict, use_map: dict):
    if type(use_map) == dict:
        new_dist = updated_map.copy()
        for k, v in get_enumerate(use_map):
            if new_dist.get(k):
                new_dist[k] = map_update(new_dist[k], v)
            else:
                new_dist[k] = v
        return new_dist
    else:
        return use_map


# dist 目标字典
# map 用来替换的字典
# retrn tuple (替换后的结果,已经替换的次数)
def template_replace(dist: any, map: dict) -> tuple:
    replace_count = 0
    if enable_enumerate(dist):
        new_dist = dist.copy()
        for k, v in get_enumerate(new_dist):
            new_dist[k], count = template_replace(v, map)
            replace_count = replace_count + count
        return (new_dist, replace_count)
    elif type(dist) == str:
        def repl_func(matched):
            nonlocal replace_count
            k = matched.group(1)
            if map.get(k):
                replace_count = replace_count + 1
                return map[k]
            return matched.group()
        replace_reslut = re.sub(r'\$([^\$]+)\$', repl_func, dist)
        return (replace_reslut, replace_count)
    else:
        return (dist, replace_count)


def load(path, encoding: str = 'utf-8'):
    return LRU_mgr.get_item(path, encoding=encoding).data_map


def save(path, aproject):
    str = yaml.dump(aproject)
    with open(path, "w") as fo:
        fo.write(str)


