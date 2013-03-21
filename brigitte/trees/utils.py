# -*- coding: utf-8 -*-
def build_path_breadcrumb(path):
    if not path:
        return []

    links = []
    cur_path = None

    for part in path.split('/'):
        if cur_path:
            cur_path += '/' + part
        else:
            cur_path = part

        links.append({
            'path': cur_path,
            'name': part,
        })

    return links
