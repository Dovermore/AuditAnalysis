import logging
from collections import defaultdict
from math import floor
from multiprocessing import Pool, cpu_count

from pandas import isnull

from utility.math_utility import binom_pmf, hypergeom_pmf
from utility.program_utility import Cached, SimpleProgressionBar, null_bar, OrderedDict, BatchFunctionWrapper

console_logger = logging.getLogger("console_logger")
console_logger.setLevel(logging.DEBUG)
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


def stochastic_process_simulation_parallel(rejection_fn, n, m, step=1, p=1/2, progression=False,
                                           replacement=False, multiprocessing_batch=30, *args, **kwargs):
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
                q.pop()
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
                    key, value = result_q.pop()
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
def stochastic_process_simulation_serial(rejection_fn, n, m, step=1, p=1/2, progression=False,
                                         replacement=False, *args, **kwargs):
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

    # Records {sample_number: power} pair for the election
    # This one only records the sample number but not the winner's vote
    cumulative_rejection = defaultdict(float)
    total_power = 0

    # While q is not empty
    while len(q):
        # get next node to explore
        key, value = q.peek()

        # Update progression
        progression_bar(key[0])

        # Last step of calculation is finished, record the total power
        if (key[0] - step) in cumulative_rejection:
            total_power += cumulative_rejection[key[0] - step]
            del cumulative_rejection[key[0] - step]

        # If sampled to the max number already, break (max number inclusive)
        if isinstance(m, int) and key[0] > m:
            break

        # Break if a power is given and already at that power
        if isinstance(m, float) and total_power >= m:
            break

        if replacement and key[0] > n:
            break

        # Remove the value
        q.pop()

        t, y_t, p_t = *key, value
        console_logger.debug(f"         poped: {t, y_t, p_t}")

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
            if isnull(p_next * p_t):
                node = (t_next, y_t_next, 0)

            # if null is rejected, put it in the risk dict
            if reject:
                rejection_dict[node[:2]] += node[2]
                cumulative_rejection[node[0]] += node[2]
            else:
                q.append(node[:2], node[2])

    # The information in this is enough to determine the result
    return rejection_dict


@Cached
def stochastic_process_simulation(*args, **kwargs):
    # TODO optimise the checking for rejection (don't need to compute the rejection after a certain point)
    multiprocessing = False
    if "multiprocessing" in kwargs:
        multiprocessing = kwargs.pop("multiprocessing")

    if multiprocessing:
        return stochastic_process_simulation_parallel(*args, **kwargs)
    else:
        return stochastic_process_simulation_serial(*args, **kwargs)


if __name__ == "__main__":
    from auditing_setup.audit_methods import *
    from time import time
    now = time()
    bayesian = Bayesian(0.99)
    rejection_dict = stochastic_process_simulation(bayesian, 100000, 2000, replacement=False)
    # rejection_dict = stochastic_process_simulation(bayesian, 1000, 1000, replacement=False)
    # rejection_dict = stochastic_process_simulation(bayesian, 100, 100, replacement=False)
    print(rejection_dict, sum(rejection_dict.values()))
    after = time()
    duration = after - now
    print(f"duration: {duration}")
    pass
