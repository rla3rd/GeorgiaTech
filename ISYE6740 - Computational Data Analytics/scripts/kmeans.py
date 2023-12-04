import sys
import time
import traceback
import numpy as np
import pandas as pd
from PIL import Image
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
from argparse import ArgumentParser

# original K-means code from CSE-6040 Homework
# modified for ISYE-6740

# %matplotlib inline
mpl.rc("savefig", dpi=100)  # Adjust for higher-resolution figures


# Helper functions from Logistic Regression Lesson
def make_scatter_plot(
    df,
    x="x_1",
    y="x_2",
    hue="label",
    palette={0: "red", 1: "olive"},
    size=5,
    centers=None
):
    sns.lmplot(
        x=x,
        y=y,
        hue=hue,
        data=df,
        palette=palette,
        fit_reg=False)
    if centers is not None:
        plt.scatter(
            centers[:, 0],
            centers[:, 1],
            marker=u'*',
            s=500,
            c=[palette[0], palette[1]])


def mark_matches(a, b, exact=False):
    """
    Given two Numpy arrays of {0, 1} labels, returns a new boolean
    array indicating at which locations the input arrays have the
    same label (i.e., the corresponding entry is True).
    This function can consider "inexact" matches. That is, if `exact`
    is False, then the function will assume the {0, 1} labels may be
    regarded as the same up to a swapping of the labels. This feature
    allows
    a == [0, 0, 1, 1, 0, 1, 1]
    b == [1, 1, 0, 0, 1, 0, 0]
    to be regarded as equal. (That is, use `exact=False` when you
    only care about "relative" labeling.)
    """
    assert a.shape == b.shape
    a_int = a.astype(dtype=int)
    b_int = b.astype(dtype=int)
    assert ((a_int == 0) | (a_int == 1)).all()
    assert ((b_int == 0) | (b_int == 1)).all()

    exact_matches = (a_int == b_int)
    if exact:
        return exact_matches

    assert exact is False
    num_exact_matches = np.sum(exact_matches)
    if (2*num_exact_matches) >= np.prod(a.shape):
        return exact_matches
    return exact_matches is False  # Invert


def count_matches(a, b, exact=False):
    """
    Given two sets of {0, 1} labels, returns the number of mismatches.
    This function can consider "inexact" matches. That is, if `exact`
    is False, then the function will assume the {0, 1} labels may be
    regarded as similar up to a swapping of the labels. This feature
    allows
    a == [0, 0, 1, 1, 0, 1, 1]
    b == [1, 1, 0, 0, 1, 0, 0]
    to be regarded as equal. (That is, use `exact=False` when you
    only care about "relative" labeling.)
    """
    matches = mark_matches(a, b, exact=exact)
    return np.sum(matches)


def init_centers_idxs(X, k):
    return np.random.randint(X.shape[1], size=(1, k))


def init_centers(X, k):
    """
    Randomly samples k observations from X as centers.
    Returns these centers as a (k x d) numpy array.
    """
    samples = init_centers_idxs(X, k)
    return X[:, samples[0]]


def compute_d_p(X, centers, p):
    c2 = np.sum(np.power(centers, p), axis=0, keepdims=True)
    S = (2 * np.dot(X.T, centers) - c2)
    return S


def assign_cluster_labels(S):
    # since the negative sign is missing from the vectorized
    # calc we can use argmax(S) or argmin(-S)
    return np.argmax(S, axis=1)


def update_centers(X, y):
    # this is still not vectorized
    # i just transposed X then returned the transposed
    # centers variable to cope for now...
    #
    # X[:m, :d] == m points, each of dimension d
    # y[:m] == cluster labels
    m, d = X.T.shape
    k = max(y) + 1
    # print(f"update centers k: {k}, y: {y}")
    # assert m == len(y)
    # assert (min(y) >= 0)
    centers = np.empty((k, d))
    for j in range(k):
        # Compute the new center of cluster j,
        # i.e., centers[j, :d].
        x_t = X.T[y == j, :]
        centers[j, :d] = np.mean(x_t, axis=0)
    return centers.T


def WCSS(S):
    return np.sum(np.amax(S, axis=1))


def has_converged(old_centers, centers):
    return set(
        [tuple(x) for x in old_centers]) == set([tuple(x) for x in centers])


def kmeans(X, k, p, max_steps=np.inf, verbose=False):

    centers = init_centers(X, k)
    # print(f"X: {X}, len X: {len(X)}")
    # print(f"init centroids: {centers}")
    converged = False
    labels = np.zeros(len(X))
    i = 1
    orig_k = k
    while (not converged) and (i <= max_steps):
        old_centers = centers
        S = compute_d_p(X, centers, p)
        labels = assign_cluster_labels(S)
        if len(set(labels)) < k:
            print(f"K: {orig_k}: Not all centroids have clusters, trying again")
            centers = init_centers(X, k)
            labels = assign_cluster_labels(S)
        else:
            centers = update_centers(X, labels)
            converged = has_converged(old_centers, centers)
            i += 1
            if verbose:
                # since our compute_d_p results in a maximum variant
                # and its not really squared, this is reeally a psuedo
                # WCSS
                print("iteration", i, "Psuedo WCSS (Max Variant)= ", WCSS(S))

    return centers, labels


def get_neighbor(X, medoids):
    # pick a random node from the set
    # if that idx is in the current cluster, pick again
    node = X[:, np.random.randint(X.shape[1], size=1)]
    node = np.squeeze(node)
    while node.tolist() in medoids.T.tolist():
        node = X[:, np.random.randint(X.shape[1], size=1)]

    # return the node
    return np.squeeze(node)


def kmedoids(X, k, p, max_neighbors=200, num_local=10, verbose=False):

    assert len(X) > 0
    assert k > 0 and k <= X.shape[1]

    mincost = np.inf
    current_best = []
    best_node = []

    i = 1
    while i <= num_local:
        node = init_centers(X, k)
        S = compute_d_p(X, node, p)
        cost = np.sum(S)
        labels = assign_cluster_labels(S)
        node_copy = node.copy()
        j = 1
        while j <= max_neighbors:
            node = np.squeeze(get_neighbor(X, node_copy))
            r_idx = np.random.randint(0, k)
            node_copy[:, r_idx] = node
            new_S = compute_d_p(X, node_copy, p)
            new_cost = np.sum(new_S)

            if new_cost < cost:
                cost = new_cost
                current_best = node_copy.copy()
                # print(f"iteration: {i}, cost: {cost}")
                # print(f"current_best: {current_best}")
                j = 1
                continue
            else:
                j += 1
                if j < max_neighbors:
                    continue
                else:
                    if cost < mincost:
                        mincost = cost
                        best_node = current_best.copy()
                        if verbose:
                            print(f"iteration: {i}, mincost: {mincost}")
                            print(f"iteration: {i}, best node: {best_node}")
            i += 1
            if i > num_local:
                S = compute_d_p(X, best_node, p)
                labels = assign_cluster_labels(S)
                return best_node, labels
            else:
                break


def read_img(path):
    """
    Read image and store it as an array, given the image path.
    Returns the 3 dimensional image array.
    """
    img = Image.open(path)
    img_arr = np.array(img, dtype='uint32')
    img.close()
    return img_arr


def display_image(arr):
    """
    display the image
    input : 3 dimensional array
    """
    arr = arr.astype(dtype='uint8')
    img = Image.fromarray(arr, 'RGB')
    plt.imshow(np.asarray(img))


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument(
        '-f',
        '--file',
        dest='file',
        default=None,
        help='bitmap image file')
    parser.add_argument(
        '-k',
        dest='k',
        default=3,
        type=int,
        help='number of clusters')
    parser.add_argument(
        '-m',
        '--mode',
        dest='mode',
        default='C',
        help='[C, M] - centroid or medoid (Default C)')
    parser.add_argument(
        '-d',
        '--distance',
        dest='distance',
        type=int,
        default=2,
        help='Distance 1 - Manhattan, 2 - Euclidean (Default 2)'
    )
    parser.add_argument(
        '-i',
        '--iterations',
        dest='num_local',
        type=int,
        default=10,
        help='max iterations (Default 10)'
    )
    parser.add_argument(
        '-n',
        '--neighbors',
        dest='neighbors',
        type=int,
        default=200,
        help='number of neighbors to sample (Default 200)'
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

    image = read_img(options.file)
    w, h, d = image.shape
    if options.verbose:
        print('Image found with width: {}, height: {}, depth: {}'.format(w, h, d))

    X = image.reshape((w * h, d))
    uniq = np.unique(X)
    if options.verbose:
        print(f"unique: {uniq.shape}")
    X = X.T
    K = options.k  # the desired number of colors in the compressed image
    if K > uniq.shape[0]:
        if options.verbose:
            print("k: {K} is greater than unique points in data set.")
            print(f"Adjusting K to {uniq}.")
        K = uniq.shape[0]
    p = options.distance
    num_local = options.num_local
    neighbors = options.neighbors

    if p not in (1, 2):
        print("distance must be between 1 or 2")
        sys.exit(0)

    try:
        start_time = time.time()
        if options.mode == 'C':
            algo_name = 'kmeans'
            centroids, labels = kmeans(X, K, p, max_steps=200, verbose=options.verbose)
            if options.verbose:
                print(f"K-means algorithm: {options}")
                print(f"centroids: {centroids}")
                print(f"labels: {labels+1}")
            labels = np.array(labels, dtype=np.uint8)
            centers = centroids

        elif options.mode == 'M':

            
            algo_name = 'kmedoids'
            medoids,  labels = kmedoids(X, K, p, max_neighbors=neighbors, num_local=num_local, verbose=options.verbose)
            if options.verbose:
                print(f"K-medoids algorithm: {options}")
                print(f"medoids: {medoids}")
                print(f"labels: {labels+1}")
            labels = np.array(labels, dtype=np.uint8)
            centers = medoids

        else:
            print("Incorrect Mode Specificied.  Must be C or M.")
            sys.exit(0)
        new_image = np.array(
                centers.T[labels, :], dtype=np.uint8).reshape((w, h, d))
        compressed_image = Image.fromarray(new_image)
        base, sfx = options.file.split('.')
        contents = 'image'
        basefile = f"{base}-{K}-{p}-{algo_name}-%s"
        if options.verbose:
            print(f"Writing image to {basefile % contents}.png")
        compressed_image.save(
            f"{basefile % contents}.png", "PNG")
        contents = "centers"
        if options.verbose:
            print(f"Writing centers to {basefile % contents}.txt")
        file = open(f"{basefile % contents}.txt", "w")
        file.write(np.array_str(centers, precision=2))
        file.flush()
        file.close()
        contents = "clusters"
        df = pd.DataFrame(data=labels)
        if options.verbose:
            print(f"Writing cluster labels to {basefile % contents}.txt")
        df.to_csv(f"{basefile % contents}.txt", "w", index=False)
        elapsed = time.time() - start_time
        if options.verbose:
            print(f"Elapsed Time: {elapsed} seconds")
    except Exception:
        err = sys.exc_info()
        details = traceback.format_exc()
        print(err, details)
