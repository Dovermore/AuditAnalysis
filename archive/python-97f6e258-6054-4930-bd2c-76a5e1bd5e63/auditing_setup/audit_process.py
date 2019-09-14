import logging
from collections import defaultdict
from math import floor
from multiprocessing import Pool, cpu_count
from auditing_setup.audit_methods import BaseMethod
from pandas import isnull
from auditing_setup.election_setting import Election
from utility.math_utility import binom_pmf, hypergeom_pmf
from utility.program_utility import Cached, SimpleProgressionBar, null_bar, OrderedDict, BatchFunctionWrapper

console_logger = logging.getLogger("console_logger")
console_logger.setLevel(logging.ERROR)
console_logger.addHandler(logging.StreamHandler())


@Cached
def index_conversion(t, y_t, step):
    """
    Convert the (t, y_t) coordinate to matrix coordinate
    """
    return step * ((t-1)*t)//2 + t + y_t  # (+1-1) due to 0 index


def single_node_update(rejection_fn, n, t, y_t, p_t, step, p, replacement, *args, **kwargs):
    rejection_dict = defaultdict(float)
    q = OrderedDict()
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
        if isnull(node[2]):
            node = (t_next, y_t_next, 0)

        # Don't add to queue or dict if there is no chance for it
        if node[2] == 0:
            continue

        # if null is rejected, put it in the risk dict
        if reject:
            rejection_dict[node[:2]] += node[2]
        else:
            q.append(node[:2], node[2])
    return rejection_dict, q


@Cached
def audit_process_simulation_parallel(rejection_fn: BaseMethod, election: Election, progression=False,
                                      multiprocessing_batch=30, *args, **kwargs):
    m = election.m
    n = election.n
    step = election.step
    replacement = election.replacement
    p = election.p

    if m == -1:
        m = n
    m += 1
    progression_bar = null_bar
    if progression:
        progression_bar = SimpleProgressionBar(m)
    rejection_dict = defaultdict(float)
    # first element: t,
    # second element: y_t, (observe every step time)
    # third element: probability going to this state
    source = (0, 0, 1)

    q = OrderedDict()
    q.append(source[:2], source[2])

    num_workers = cpu_count()

    for i in range(0, m, step):
        # get next node to explore
        key, value = q.peek()

        console_logger.info(f"    Start Pool: {i}")
        async_results = []

        with Pool(num_workers) as pool:
            # Instantiate first wrapper
            batch_function_wrapper = BatchFunctionWrapper()
            total = 0
            while key[0] <= i:
                # logging.info(f"Queue = {q}")
                assert key[0] == i
                # Remove the value
                q.popitem(last=False)
                t, y_t, p_t = *key, value
                console_logger.debug(f"         poped: {t, y_t, p_t}")
                # If the batch processor already full, send to another process to process
                if len(batch_function_wrapper) >= multiprocessing_batch:
                    total += 1
                    async_result = pool.apply_async(batch_function_wrapper, ())
                    async_results.append(async_result)
                    batch_function_wrapper = BatchFunctionWrapper()

                batch_function_wrapper.add_call(single_node_update, rejection_fn, n, t, y_t, p_t,
                                                step, p, replacement, *args, **kwargs)
                if not len(q):
                    break
                key, value = q.peek()
            # If there is still calls left un processed, send to a process.
            if len(batch_function_wrapper):
                async_result = pool.apply_async(batch_function_wrapper, ())
                async_results.append(async_result)
            console_logger.info(f"Total sent to process = {total + 1}")

            # Wait for all the processes to finish and update the results
            console_logger.info("        waiting result:")
            all_results = []
            for async_result in async_results:
                all_results += async_result.get()

            for result_rejection_dict, result_q in all_results:
                # logging.debug("--------------------")
                # logging.debug(result_rejection_dict)
                # logging.debug(result_q)
                for key, value in result_rejection_dict.items():
                    rejection_dict[key] += value
                while len(result_q):
                    key, value = result_q.popitem(last=False)
                    q.append(key, value)
        console_logger.info(f"    End   Pool: {i}")
        # Update progression
        progression_bar(key[0])
        # Break if no more item remains (all rejected)
        if not len(q):
            break

    # The information in this is enough to determine the result
    return rejection_dict


@Cached
def audit_process_simulation_serial(rejection_fn, election: Election, progression=False, *args, **kwargs):

    m = election.m
    n = election.n
    step = election.step
    replacement = election.replacement
    p = election.p

    if m == -1:
        m = n + 1

    w = floor(n * p)

    progression_bar = null_bar

    if progression:
        progression_bar = SimpleProgressionBar(m)

    rejection_dict = defaultdict(float)

    # first element: t,
    # second element: y_t, (observe every step time)
    # third element: probability going to this state
    source = (0, 0, 1)

    q = OrderedDict()
    q.append(source[:2], source[2])

    # While q is not empty
    while len(q):
        # get next node to explore
        key, value = q.peek()

        # Update progression
        progression_bar(key[0])

        # If sampled to the max number already, break (max number exclusive)
        if isinstance(m, int) and key[0] >= m:
            break

        if replacement and key[0] > n:
            break

        # Remove the value
        q.popitem(last=False)

        t, y_t, p_t = *key, value
        console_logger.debug(f"         poped: {t, y_t, p_t}")

        t_next = t + step

        n_remain = n - t
        w_remain = w - y_t

        reject = False
        # All possible generated sa for next batch
        for i in range(0, step+1):
            y_t_next = y_t + i

            if not replacement:
                # If no replacement sample from hypergeometric distribution
                p_next = hypergeom_pmf(i, n_remain, w_remain, step)
            else:
                # Else use binomial compute probability
                p_next = binom_pmf(i, step, p)

            # Update reject if it's False, don't need to compute reject if it's True already (as is tested sequentially)
            if not reject:
                # Remainder: Don't use is to compare True False
                reject = rejection_fn(n, t_next, y_t_next, *args, **kwargs)

            # Compose the node
            node = (t_next, y_t_next, p_next * p_t)
            if isnull(p_next * p_t):
                node = (t_next, y_t_next, 0)

            # if null is rejected, put it in the risk dict
            if reject:
                rejection_dict[node[:2]] += node[2]
            else:
                q.append(node[:2], node[2])

    # The information in this is enough to determine the result
    return rejection_dict


def audit_process_simulation(*args, **kwargs):
    if "multiprocessing_batch" in kwargs:
        return audit_process_simulation_parallel(*args, **kwargs)
    else:
        return audit_process_simulation_serial(*args, **kwargs)


if __name__ == "__main__":
    from auditing_setup.audit_methods import *
    from time import time
    now = time()
    election = Election(n=500, m=500, replacement=False, step=250, p=0.5)
    # audit_function = TruncatedBayesian(0.05)
    audit_function = Clip(alpha=0.7, election=election)
    rejection_dict = audit_process_simulation_serial(audit_function, election)
    print(rejection_dict)
    print(sum(rejection_dict.values()))
    after = time()
    duration = after - now
    print(f"duration: {duration}")
    pass
