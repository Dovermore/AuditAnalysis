import logging
from multiprocessing import Pool
from utility.program_utility import (Cached, SimpleProgressionBar, null_bar, AutoLockMultiprocessingDefaultdict, AutoLockMultiprocessingOrderedDict, CollectionsManager)
from utility.math_utility import binom_pmf
import scipy as sp

from math import floor



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
                    transition_matrix.loc[index, index_next] = binom_pmf(y_t_add, step, p_h0)
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


def single_node_update(rejection_dict, q, rejection_fn, n, t, y_t, p_t, step, p, replacement, *args, **kwargs):
    # Take the floor for winner's share
    w = floor(n * p)

    t_next = t + step
    n_remain = n - t
    w_remain = w - y_t

    # All possible generated sa for next batch
    for i in range(step+1):
        y_t_next = y_t + i

        if not replacement:
            # If no replacement sample from hypergeometric distribution
            p_next = hypergeom_pmf(i, n_remain, w_remain, step)
        else:
            # Else use binomial compute probability
            p_next = binom_pmf(i, step, p)

        # Is this state rejected?
        reject = rejection_fn(n, t_next, y_t_next, *args, **kwargs)

        # Compose the node
        node = (t_next, y_t_next, p_next * p_t)
        if pd.isnull(node[2]):
            node = (t_next, y_t_next, 0)

        logging.debug(f"rejection({[n, t, y_t]}): {reject}")
        # No need for a lock since the Data Structures inherently have locks in their method
        # if null is rejected, put it in the risk dict
        if reject:
            logging.debug(f"        rejected: {node[:2]} -> {node[2]}")
            rejection_dict[node[:2]] += node[2]
        else:
            logging.debug(f"        append queue: {node[:2]} -> {node[2]}")
            q.append(node[:2], node[2])


def stochastic_process_simulation(rejection_fn, n, m, step=1, p=1/2, progression=False,
                                  replacement=False, *args, **kwargs):
    # manager for multiprocessing purpose
    mgr = CollectionsManager()
    mgr.start()

    if m == -1:
        m = n
    m += 1

    progression_bar = null_bar

    if progression:
        progression_bar = SimpleProgressionBar(m)

    rejection_dict = AutoLockMultiprocessingDefaultdict(float, mgr)

    # first element: t,
    # second element: y_t, (observe every step time)
    # third element: probability going to this state
    source = (0, 0, 1)

    q = AutoLockMultiprocessingOrderedDict(mgr)
    q.append(source[:2], source[2])

    for i in range(0, m, step):
        # get next node to explore
        logging.debug(f"{i}")
        key, value = q.peek()

        logging.debug(f"    Start Pool: {i}")
        with Pool() as pool:
            while key[0] <= i:
                assert key[0] == i
                # Remove the value
                q.pop()
                t, y_t, p_t = *key, value
                logging.debug(f"*        poped: {t, y_t, p_t}")
                pool.apply_async(single_node_update, (rejection_dict, q, rejection_fn, n, t, y_t, p_t, step, p,
                                                      replacement, *args), kwargs)
                if not len(q):
                    break
                key, value = q.peek()
        logging.debug(f"    End   Pool: {i}")
        # Update progression
        progression_bar(key[0])

        # Break if no more item remains (all rejected)
        if not len(q):
            break

    # The information in this is enough to determine the result
    return rejection_dict


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    from auditing_setup.audit_methods import *
    from time import process_time
    now = process_time()
    bayesian = Bayesian(0.99)
    stochastic_process_simulation(bayesian, 100000, 5000, replacement=True)
    after = process_time()
    duration = after - now
    print(f"duration: {duration}")
    pass
