import os
import sys
import re
import hashlib
from tqdm import tqdm
from soviby import helper_yaml


def myexcepthook(type, value, traceback, oldhook=sys.excepthook):
    oldhook(type, value, traceback)
    input("Press RETURN. ")


sys.excepthook = myexcepthook


class CommandLineParser:
    def __init__(self):
        self.desc_map = {}

    # 返回指令集说明字符，list<str>
    def show_comm_list(self, arg_symbol: tuple = ('<', '>')):
        str_list = []

        def show_comm(desc):
            if desc.get('is_print'):
                desc['is_print'] = False
                return
            name = desc.get('name')
            alias = desc.get('alias')
            referral = desc.get('referral')
            kind = desc.get('kind')

            name_str = '-' + name
            alias_str = ', -' + alias if alias else ''
            kind_str = f'{arg_symbol[0]}{kind}{arg_symbol[1]}' if kind else ''
            referral_str = referral if referral else ''

            str_list.append(
                f'{name_str}{alias_str} {kind_str}    {referral_str}')
            desc['is_print'] = alias
        for k, v in self.desc_map.items():
            show_comm(v)
        return str_list

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
            if i < argc - 1:
                val = argv[i + 1]
                kind = desc['kind']
                val = handle_type(val, kind)
            func = desc['func']
            if func:
                def _func():
                    if val:
                        return func(val)
                    else:
                        return func()
                ret[name] = _func
            else:
                ret[name] = val

        return ret

    def handle_command(self, command_list: list, env: dict = None):
        com_dict = self.parse(command_list)
        result = None
        for k, v in com_dict.items():
            if type(v) == type(lambda: True):
                result = v()
            else:
                if env and env.get(k):
                    env[k] = v
        return result


def handle_command(com_parser: CommandLineParser, command_list: list, env: dict = None):
    assert com_parser, 'com_parser is none.'
    return com_parser.handle_command(command_list, env)


def handle_sys_argv_command(com_parser: CommandLineParser):
    assert com_parser, 'com_parser is none.'
    sys_args = sys.argv[1:]
    if not sys_args:
        return
    handle_command(com_parser, sys_args)


def show_commands(com_parser: CommandLineParser):
    comm_list = com_parser.show_comm_list()
    print('Show Commands:')
    for i, v in enumerate(comm_list):
        print(v)


def set_command_exit(com_parser: CommandLineParser):
    print('输入-exit或-e后退出.(-help或-h查看所有指令)')
    com_parser.add_desc(name='exit', alias='e',
                        func=sys.exit, referral='Exit.')


# 设置输入循环
def set_input_loop(com_parser: CommandLineParser, env: dict = None):
    com_parser.add_desc(name='help', alias='h',
                        func=lambda: show_commands(com_parser), referral='Show help.')
    set_command_exit(com_parser)
    while True:
        command_str = input('>')
        if not command_str:
            continue
        command_list = command_str.split(' ')
        result = handle_command(com_parser, command_list, env)
        if result:
            print(result)


def get_md5(data: bytes):
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()


# 格式化路径
# 通过filedialog.askopenfilename获得的路径是以"/"分割
def get_format_path(path):
    return re.sub(r'(\\|\/)+', r'\\\\', path)


def get_exe_path():
    return os.path.split(os.path.abspath(sys.argv[0]))


# 读取配置,yaml格式
# 返回 字典:key(string)->value(string)
def read_config_by_yml(path: str, func, encoding: str = 'utf-8') -> dict:
    yml_data = helper_yaml.load(path,encoding)
    func(yml_data.data_map)

    
# 读取配置 ,以=为分割
# 返回 字典:key(string)->value(string)
def read_config_by_str(path: str, encoding: str = 'utf-8') -> dict:
    ret = {}
    with open(path, 'r', encoding=encoding) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            splits = line.split('=')
            if len(splits) < 2:
                continue
            ret[splits[0]] = splits[1]
    return ret


# 路径中是否存在符合条件的文件
def walk_tree(root: str, pred, is_show_pbar=False):
    pbar = None
    listdir = os.listdir(root)
    if is_show_pbar:
        pbar = tqdm(total=len(listdir))
        pbar.set_description(f'walk {root}:')

    dirs = []
    for f in listdir:
        path = os.path.join(root, f)
        if os.path.isdir(path):
            dirs.append(path)
        else:
            if pbar:
                pbar.update()
            if pred(path):
                return True
    for f in dirs:
        if pbar:
            pbar.update()
        if walk_tree(f, pred, is_show_pbar):
            return True
    if pbar:
        pbar.close()
    return False


def rgba2hex(r, g, b):
    return ('{:02X}' * 3).format(r, g, b)


def hex2rgba(hex):
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

