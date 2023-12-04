import numpy as np
import kmeans
import csv
import sys
from matplotlib import pyplot as plt
from argparse import ArgumentParser

np.set_printoptions(threshold=sys.maxsize)

def spectral(k, nodes, edges):
    m = len(nodes)
    # create empty adjacency matrix
    A = np.zeros((m, m))
    # make adjacency matrix symmetric
    for edge in edges:
        A[edge[0]-1, edge[1]-1] = 1
        A[edge[1]-1, edge[0]-1] = 1

    # get non zero rows
    nz = (np.where(A.any(axis=0))[0])
    # get the non zero rows and colunms to
    # form the final adjacency matrix
    A = np.take(A, nz, axis=0)
    A = np.take(A, nz, axis=1)
    m, n = A.shape
    if options.verbose:
        print(f"Adjacency Matrix shape: {A.shape}")
        # print(f"Adjacency Matrix: {A}")

    D = np.diag(np.sum(A, axis=1))
    L = D - A

    # use svd() instead of eig, to make sure the eigenvalues are sorted
    x, v, _ = np.linalg.svd(L)
    x = np.flip(x, 1)
    x = x[:, 0:k].real
    if options.verbose:
        # print(f"eigenvectors: {x}")
        pass

    # k-means
    # X needs transposed for this implementation
    centroids, labels = kmeans.kmeans(x.T, k, 2)
    if options.verbose:
        print(f"centroids: {centroids}")
        print(f"labels: {labels}")
        print(f"nodes: {nodes}")

    clusters = []
    for i in range(len(labels)):
        nz_idx = nz[i] + 1
        node = nodes[nz_idx]
        label = labels[i]
        centroid = centroids[label]
        if options.verbose:
            print(f"label: {label}, affiliation: {node['affiliation']},  centroid: {centroid}")
        clusters.append([label, int(node['affiliation']), centroid])

    clusters = np.array(clusters, dtype=object).T
    predict = []
    mismatch = []
    counts = []
    for i in range(len(centroids)):
        cls_idx = np.where(clusters[0, :] == i)
        C = np.take(clusters, cls_idx, axis=1)
        if C[1].shape[1] > 0:
            if options.verbose:
                print(f"predict pct: {np.sum(C[1])/C[1].shape[1]}, predict label: {np.round(np.sum(C[1])/C[1].shape[1])}, predict sum: {np.sum(C[1])}, predict count: {C[1].shape[1]}")
            majority = np.round(np.sum(C[1])/C[1].shape[1])
            predict.append(majority)
            mismatches = np.abs(majority - C[1])
            mismatch_rate = np.sum(mismatches)/mismatches.shape[1]
            mismatch.append(mismatch_rate)
            counts.append(mismatches.shape[1])

    mismatch = np.array(mismatch)
    rates = mismatch * counts
    total_rate = np.sum(rates)
    total_counts = np.sum(counts)
    mismatch_rate = total_rate/total_counts

    return predict, mismatch, mismatch_rate

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-k',
        dest='k',
        default=20,
        type=int,
        help='number of clusters')
    parser.add_argument(
        '-m',
        '--maxmode',
        dest='maxmode',
        action='store_true',
        default=False,
        help='maxmode: loop over k from 2 to k'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        dest='verbose',
        action='store_true',
        default=False,
        help='verbose mode'
    )

    options = parser.parse_args()

    k = options.k

    nodes = {}
    edges = []
    file = open('data/nodes.txt')
    csv.reader(file)
    lines = file.readlines()
    nodes_array = [line.replace('\n', '').split('\t') for line in lines]
    for node in nodes_array:
        nodes[int(node[0])] = {
            'name': node[1],
            'affiliation': node[2],
            'label': node[3]}

    file = open('data/edges.txt')
    lines = file.readlines()
    edges_array = [line.replace('\n', '').split('\t') for line in lines]
    if options.verbose:
        print(f"len edges: {len(edges_array)}")
    for edge in edges_array:
        if edge[0] != edge[1]:
            edges.append([int(edge[0]), int(edge[1])])
    if options.verbose:
        msg = ":".join([
            "len edges after self referencing node removal"
            f" {len(edges_array)}"])
        print(msg)

    edges = np.array(edges)
    if options.maxmode:

        Ks = range(2, k+1)
        rates = []
        for k in Ks:
            predict, mismatches, mismatch_rate = spectral(k, nodes, edges)
            print(f"k={k}, mismatch rate: {mismatch_rate}")  
            rates.append([k, mismatch_rate])

        rates = np.array(rates)
        x = rates.T[0]
        y = rates.T[1]
        plt.plot(x, y)    
        plt.xlabel("Values of k")
        plt.ylabel("Mismatch Rate")
        plt.title("Spectral Clustering Mismatch Rate")

        plt.show()

    else:
        predict, mismatches, mismatch_rate = spectral(k, nodes, edges)
        print(f"k={k}, majorities={predict}, mismatches: {mismatches}, mismatch rate: {mismatch_rate}")  

