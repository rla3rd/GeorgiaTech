import http.client
import json
import time
import timeit
import sys
import collections
from pygexf.gexf import *
import argparse
import urllib.request
import pickle
import os

parser = argparse.ArgumentParser()
parser.add_argument("key")
args = parser.parse_args()

#
# implement your data retrieval code here
#


def get_lego_sets():
    pickle_file_name = 'sets.pickle'
    if os.path.exists(pickle_file_name):
        pickle_file = open(pickle_file_name, 'rb')
        sets = pickle.load(pickle_file)
    else:
        pickle_file = open(pickle_file_name, 'wb')
        sets = []
        url = 'https://rebrickable.com/api/v3/lego/sets/'
        url += '?&page_size=300&min_parts=%s&key=%s' % (min_parts(), args.key)
        with urllib.request.urlopen(url) as res:
            res = json.loads(res.read())
            for s in res['results']:
                sets.append({'id': s['set_num'], 'name': s['name']})
        pickle.dump(sets, pickle_file)
    return sets


def get_parts(set_id):
    code = 0
    while code != 200:
        url = 'https://rebrickable.com/api/v3/lego/sets/'
        url += '%s/parts/?&page_size=1000&key=%s' % (set_id, args.key)
        res = urllib.request.urlopen(url)
        if res.code == 429:
            time.sleep(2)
        code = res.code
        results = json.loads(res.read())
        parts = results['results']
    return parts


def lego_parts(set_id):
    parts = get_parts(set_id)
    quantities = {}
    for p in parts:
        quantities[p['quantity']] = {
            'part_num': p['part']['part_num'],
            'color': p['color']['rgb'],
            'name': p['part']['name'],
            'quantity': p['quantity']}
    keys = sorted(list(quantities.keys()), reverse=True)[:20]
    top_parts = []
    for key in keys:
        top_parts.append(quantities[key])

    return top_parts


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# complete auto grader functions for Q1.1.b,d
def min_parts():
    """
    Returns an integer value
    """
    # you must replace this with your own value
    return 1100


def lego_sets():
    """
    return a list of lego sets.
    this may be a list of any type of values
    but each value should represent one set

    e.g.,
    biggest_lego_sets = lego_sets()
    print(len(biggest_lego_sets))
    > 280
    e.g., len(my_sets)
    """
    # you must replace this line and return your own list
    sets = get_lego_sets()
    return sets


def gexf_graph():
    """
    return the completed Gexf graph object
    """
    sets = get_lego_sets()

    pickle_file_name = 'parts_per_set.pickle'
    if os.path.exists(pickle_file_name):
        pickle_file = open(pickle_file_name, 'rb')
        parts_per_set = pickle.load(pickle_file)
    else:
        parts_per_set = {}
        for s in sets:
            set_parts = lego_parts(s['id'])
            parts_per_set[s['id']] = set_parts
        pickle_file = open(pickle_file_name, 'wb')
        pickle.dump(parts_per_set, pickle_file)

    parts = {}
    for s in sets:
        set_parts = parts_per_set[s['id']]
        for part in set_parts:
            p = part.copy()
            key = '%s_%s' % (p['part_num'], p['color'])
            parts[key] = p
            parts[key].pop('quantity')

    # you must replace these lines and supply your own graph
    gxf = Gexf("Richard Albright", "rebrickable graph file")
    graph = gxf.addGraph("undirected", "static", "rebrickable graph")
    type_attr = graph.addNodeAttribute("Type", type="string")
    color_attr = graph.addNodeAttribute("Color", type="string")
    for s in sets:
        node = graph.addNode(
            id=str(s["id"]),
            label=str(s["name"]),
            r="0",
            g="0",
            b="0")
        node.addAttribute(type_attr, 'set')
    for key in parts:
        color = '#%s' % parts[key]['color']
        (r, g, b) = hex_to_rgb(color)
        if not graph.nodeExists(str(key)):
            node = graph.addNode(
                id=str(key),
                label=str(parts[key]['name']),
                r=str(r),
                g=str(g),
                b=str(b))
            node.addAttribute(type_attr, 'part')
            node.addAttribute(color_attr, parts[key]['color'])
    for s in sets:
        pps = parts_per_set[s['id']]
        for p in pps:
            graph.addEdge(
                '%s-%s-%s' % (s['id'], str(p['part_num']), str(p['color'])),
                s['id'],
                '%s_%s' % (str(p['part_num']), str(p['color'])),
                weight=p['quantity'])
    gxf_file = open('bricks_graph.gexf', 'wb')
    gxf.write(gxf_file)
    return gxf.graphs[0]

# complete auto-grader functions for Q1.2.d


def avg_node_degree():
    """
    hardcode and return the average node degree
    (run the function called “Average Degree”) within Gephi
    """
    # you must replace this value with the avg node degree
    return 5.125


def graph_diameter():
    """
    hardcode and return the diameter of the graph
    (run the function called “Network Diameter”) within Gephi
    """
    # you must replace this value with the graph diameter
    return 10


def avg_path_length():
    """
    hardcode and return the average path length
    (run the function called “Avg. Path Length”) within Gephi
    :return:
    """
    # you must replace this value with the avg path length
    return 4.504


if __name__ == '__main__':
    gexf_graph()
