
from re import S


class LRUItem(object):
    def __init__(self):
        self.next = None
        self.prev = None
        self.content = None
        self.attach_count = 0
        self.id = None


class LRUManager(object):
    def __init__(self, create_func, destroy_func, old_capacity: int = 3, young_capacity: int = 5, old_threshold: int = 2):
        self.old_capacity = old_capacity  # old 最大容量
        self.young_capacity = young_capacity  # young 最大容量
        self.old_threshold = old_threshold  # Old 门槛   ,需要超过门槛
        self.item_map = {}
        self.old_count = 0
        self.young_count = 0
        self.young_head = None
        self.young_tail = None
        self.old_head = None
        self.old_tail = None
        self.create_func = create_func
        self.destroy_func = destroy_func

    def get_item(self, path: str, **kwargs):
        id = kwargs.get('id') if kwargs.get('id') else path
        # 查找 item_map，若没有则创建
        # 刷新激活次数
        # 返回item content
        item = self.item_map.get(id)
        if not item:
            item = LRUItem()
            item.id = id
            content = self.create_func(path, kwargs)
            item.content = content
            self.item_map[id] = item

        self.attach_item(item)
        return item.content

    def destroy_item(self, item: LRUItem):
        self.destroy_func(item.content)
        attach_count = item.attach_count
        if attach_count < self.old_threshold:
            self.young_head, self.young_tail, self.young_count = unlink_item(
                item, self.young_head, self.young_tail, self.young_count)
        else:
            self.old_head, self.old_tail, self.old_count = unlink_item(
                item, self.old_head, self.old_tail, self.old_count)
        self.item_map.pop(item.id)

    # 激活item
    def attach_item(self, item: LRUItem):
        attach_count = item.attach_count
        if attach_count > self.old_threshold:
            if self.old_head != item:
                self.old_head, self.old_tail, self.old_count = unlink_item(
                    item, self.old_head, self.old_tail, self.old_count)
                self.old_head, self.old_tail, self.old_count = link_item(
                    item, self.old_head, self.old_tail, self.old_count)
        elif attach_count == 0:
            self.young_head, self.young_tail, self.young_count = link_item(
                item, self.young_head, self.young_tail, self.young_count)
            if self.young_count > self.young_capacity:
                self.destroy_item(self.young_tail)
        elif attach_count < self.old_threshold:
            if self.young_head != item:
                self.young_head, self.young_tail, self.young_count = unlink_item(
                    item, self.young_head, self.young_tail, self.young_count)
                self.young_head, self.young_tail, self.young_count = link_item(
                    item, self.young_head, self.young_tail, self.young_count)
        else:
            self.young_head, self.young_tail, self.young_count = unlink_item(
                item, self.young_head, self.young_tail, self.young_count)
            self.old_head, self.old_tail, self.old_count = link_item(
                item, self.old_head, self.old_tail, self.old_count)
            if self.old_count > self.old_capacity:
                self.destroy_item(self.old_tail)

        item.attach_count = attach_count + 1


def link_item(item: LRUItem, out_head: LRUItem, out_tail: LRUItem, out_count: int):
    if out_head is None:
        item.next = None
        item.prev = None
        out_head = out_tail = item
    else:
        out_head.prev = item
        item.next = out_head
        item.prev = None
        out_head = item
    out_count = out_count + 1
    return out_head, out_tail, out_count


def unlink_item(item: LRUItem, out_head: LRUItem, out_tail: LRUItem, out_count: int):
    if item.prev:
        item.prev.next = item.next
    if item.next:
        item.next.prev = item.prev
    if out_head == item:
        out_head = item.next
    if out_tail == item:
        out_tail = item.prev
    item.prev = item.next = None
    out_count = out_count - 1
    return out_head, out_tail, out_count

