
import os
import sys
import re
import hashlib


class CommandLineParser:
    def __init__(self):
        self.desc_map = {}

    def show_comm_list(self, ):
        print(f'Commands:')

        def show_comm(desc):
            if desc.get('is_print'):
                desc['is_print'] = False
                return
            name = desc.get('name')
            alias = desc.get('alias')
            referral = desc.get('referral')
            kind = desc.get('kind')
            func = desc.get('func')

            name_str = '-' + name
            alias_str = ', -' + alias if alias else ''
            kind_str = f'<{kind}>' if kind else ''
            referral_str = referral if referral else ''

            print(f'{name_str}{alias_str} {kind_str}\t{referral_str}')
            desc['is_print'] = alias

        for k, v in self.desc_map.items():
            show_comm(v)

    def add_desc(self, name: str, alias: str = None, kind: str = None, default: any = None, func: any = None, referral: str = None):
        desc = {
            'name': name,
            'alias': alias,
            'kind': kind,
            'default': default,
            'func': func,
            'referral': referral,
        }
        self.desc_map[name] = desc
        if not alias is None:
            self.desc_map[alias] = desc

    def parse_dict(self, argv: dict):
        list = []
        for key, value in argv.items():
            list.append('-' + key)
            list.append(value)
        return self.parse(list, 0)

    def parse(self, argv: list[str], offset: int = 0):
        ret = {}
        argc = len(argv)

        def handle_type(val: str, kind: str):
            if kind == 'none':
                return None
            if kind == 'str':
                return str(val)
            elif kind == 'float':
                return float(val)
            elif kind == 'bool':
                return bool(int(val))
            elif kind == 'int':
                return int(val)
            elif kind == 'path':
                return get_format_path(handle_type(val, 'str'))
            elif not re.search(r'^list\[(.+)\]', kind) is None:
                match_obj = re.search(r'^list\[(.+)\]', kind)
                base_type = match_obj.group(1)
                str_list = val.split('|')
                val_list = []
                for str_item in str_list:
                    val_list.append(handle_type(str_item, base_type))
                return val_list

        for i in range(offset, argc):
            arg = argv[i]
            if not arg.startswith('-'):
                continue
            key = arg[1:]
            desc = self.desc_map.get(key)
            if desc is None:
                continue
            val = desc['default']
            name = desc['name']
            if i < argc - 1 and not argv[i + 1].startswith('-'):
                val = argv[i + 1]
                kind = desc['kind']
                val = handle_type(val, kind)
            func = desc['func']
            if func:
                def _func():
                    if val:
                        func(val)
                    else:
                        func()
                ret[name] = _func
            else:
                ret[name] = val

        return ret


# 设置输入循环
def set_input_loop(com_parser: CommandLineParser, env: dict = None):
    com_parser.add_desc(name='help', alias='h',
                        func=com_parser.show_comm_list, referral='Show help.')
    print('输入-exit或-e后退出.(-help或-h查看所有指令)')
    com_parser.add_desc(name='exit', alias='e', func=sys.exit,)
    while True:
        command_str = input('请输入指令：')
        if not command_str:
            continue
        command_list = command_str.split(' ')
        com_dict = com_parser.parse(command_list)
        for k, v in com_dict.items():
            if type(v) == type(lambda: True):
                v()
            else:
                if env and env.get(k):
                    env[k] = v


def get_md5(data):
    return hashlib.md5(data).hexdigest()


# 格式化路径
# 通过filedialog.askopenfilename获得的路径是以"/"分割
def get_format_path(path):
    return re.sub(r'(\\|\/)+', r'\\\\', path)


def get_exe_dir():
    argv = sys.argv
    return os.path.dirname(argv[0])


# 读取配置
# 返回 字典:key(string)->value(string)
def read_init_config(path: str, encoding: str = 'utf-8') -> dict:
    ret = {}
    with open(path, 'r', encoding=encoding) as f:
        for line in f.readlines():
            line = line.strip()
            splits = line.split('=')
            if len(splits) < 2:
                continue
            ret[splits[0]] = splits[1]
    return ret


# 路径中是否存在符合条件的文件
def walk_tree(root: str, pred):
    dirs = []
    for f in os.listdir(root):
        path = os.path.join(root, f)
        if os.path.isdir(path):
            dirs.append(path)
        else:
            if pred(path) == True:
                return True
    for f in dirs:
        if walk_tree(f, pred) == True:
            return True
    return False


# if __name__ == '__main__':
#     cmd_parser = CommandLineParser()
#     cmd_parser.add_desc(name='test', kind='float',
#                         func=lambda v: print(f'111:{v}'), default=0.7)
#     cmd_parser.add_desc(name='size', kind='float', default=1.0, referral='lalalalalalalalallala')
#     set_input_loop(cmd_parser)
