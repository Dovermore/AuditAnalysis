from utility import (Cached, binom, SimpleProgressionBar,
                     OrderedDict)

import scipy as sp
import numpy as np
import pandas as pd

from collections import defaultdict as dd


@Cached
def index_conversion(t, y_t, step):
    """
    Convert the (t, y_t) coordinate to matrix coordinate
    """
    return step * ((t-1)*t)//2 + t + y_t  # (+1-1) due to 0 index


@Cached
def reverse_conversion(step, index):
    t = 0
    total = 0
    while total < index:
        t += 1
        total += (t * step + 1)
    return t, t * step - (total - index)


@Cached
def binom_pmf(k, n, p):
    return binom.pmf(k, n, p)


def find_terminal(f, n, m=1, step=10, p_h0=1/2, to_sequence=False,
                  transition=False):
    """
    Find the terminal state given a specific setting
    :param f: The auditing function
    :param n: Number of total ballots
    :param m: Max number to be sampled
    :param step: How many ballots is sampled each step
    :param p_h0: p under null hypothesis
    :param to_sequence: If the output should be a pd.sequence (or dict)
    :param transition: Should return only transition probabilities (for debug)
    """
    # 1 + step+1 + 2*step+1 + 3*step+1 +...+ m*step+1 = step*((m-1)*m)/2+(m+1)
    rejections = set()

    # Initialise a DataFrame as dense matrix
    indexes = []
    for t in range(m + 1):
        total = t * step
        for y_t in range(total + 1):
            indexes.append(str((t * step, y_t)))
    transition_matrix = pd.DataFrame(0, columns=indexes, index=indexes)

    for t in range(m + 1):
        total = t * step
        for y_t in range(total + 1):
            index = str((total, y_t))
            # Rejected?
            if f(n, total, y_t):
                transition_matrix.loc[index, index] = 1
                rejections.add(index)
            # Already last layer
            elif t == m:
                transition_matrix.loc[index, index] = 1
            else:
                t_next = t + 1
                for y_t_add in range(step+1):
                    y_t_next = y_t + y_t_add
                    index_next = str((t_next * step, y_t_next))
                    transition_matrix.loc[index, index_next] = \
                        binom_pmf(y_t_add, step, p_h0)
    if transition:
        return transition_matrix
    # Initialise the sparse matrix to sovle this chain
    # transition_matrix = sp.sparse.csr_matrix(transition_matrix)
    stationary = solve_stationary(transition_matrix.values)
    d = {indexes[i]: np.asscalar(stationary[i]) for i in range(len(indexes))}
    if to_sequence:
        return pd.Series(d), rejections
    # TODO clean this up!
    return d, rejections


def convert_to_sequence(array, m, step):
    d = {}
    for t in range(m + 1):
        for y_t in range(t*step + 1):
            index = index_conversion(t, y_t, step)
            d[(t * step, y_t)] = np.asscalar(array[index])
    return pd.Series(d)


def solve_stationary(chain):
    """ x = xA where x is the answer
    x - xA = 0
    x( I - A ) = 0 and sum(x) = 1
    """
    n = chain.shape[0]
    a = np.eye(n) - chain
    a = np.vstack((a.T, np.ones(n)))
    b = np.matrix([0] * n + [1]).T
    return sp.linalg.lstsq(a, b)[0]


def stochastic_process_simulation(rejection_fn, n, m=1000, step=1, p=1/2,
                                  progression=False, *args, **kwargs):
    progression_bar = null_bar

    if progression:
        progression_bar = SimpleProgressionBar(m)
    rejection_dict = dd(float)

    # first element: t,
    # second element: y_t, (observe every step time)
    # third element: probability going to this state
    source = (0, 0, 1)

    q = OrderedDict()
    q.append(source[:2], source[2])

    while True:
        # get next node to explore
        key, value = q.peek()

        progression_bar(key[0])

        if key[0] >= m:
            break
        q.pop()
        t, y_t, p_t = *key, value

        t_next = t + step
        # All possible generated sa for next batch
        for i in range(step+1):
            # the binomial probability reaching next node
            p_binom = binom_pmf(i, step, p)

            y_t_next = y_t + i

            # rejection?
            reject = rejection_fn(n, t_next, y_t_next, *args, **kwargs)

            # Compose the node
            node = (t_next, y_t_next, p_binom * p_t)

            # if null is rejected, put it in the risk dict
            if reject:
                rejection_dict[node[:2]] += node[2]
            else:
                q.append(node[:2], node[2])

    # The information in this is enough to determine the result
    return rejection_dict


def null_bar():
    """
    This progression bar is very lazy, and does nothing!
    """
    return None


if __name__ == "__main__":
    pass
