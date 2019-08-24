import logging
from collections import defaultdict
from math import floor
from multiprocessing import Pool, cpu_count

from pandas import isnull

from utility.math_utility import binom_pmf, hypergeom_pmf
from utility.program_utility import Cached, SimpleProgressionBar, null_bar, OrderedDict, BatchFunctionWrapper

logging.getLogger().setLevel(logging.INFO)


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

        # No need for a lock since the Data Structures inherently have locks in their method
        # if null is rejected, put it in the risk dict
        if reject:
            rejection_dict[node[:2]] += node[2]
        else:
            q.append(node[:2], node[2])
    return rejection_dict, q


def stochastic_process_simulation(rejection_fn, n, m, step=1, p=1/2, progression=False,
                                  replacement=False, multiprocessing_batch=50, *args, **kwargs):
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

        logging.info(f"    Start Pool: {i}")
        async_results = []

        with Pool(num_workers) as pool:
            # Instantiate first wrapper
            batch_function_wrapper = BatchFunctionWrapper()
            total = 0
            while key[0] <= i:
                assert key[0] == i
                # Remove the value
                q.pop()
                t, y_t, p_t = *key, value
                logging.info(f"         poped: {t, y_t, p_t}")

                # If not the number of batches yet, add to current batch
                if len(batch_function_wrapper) < multiprocessing_batch:
                    batch_function_wrapper.add_call(single_node_update, rejection_fn, n, t, y_t, p_t,
                                                    step, p, replacement, *args, **kwargs)
                # If the batch processor already full, send to another process to process
                else:
                    total += 1
                    logging.info(f"Total sent to process = {total}")
                    async_result = pool.apply_async(batch_function_wrapper, ())
                    async_results.append(async_result)
                    batch_function_wrapper = BatchFunctionWrapper()

                if not len(q):
                    break
                key, value = q.peek()
            # If there is still calls left un processed, send to a process.
            if len(batch_function_wrapper):
                async_result = pool.apply_async(batch_function_wrapper, ())
                async_results.append(async_result)

            # Wait for all the processes to finish and update the results
            logging.info("        waiting result:")
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
        logging.info(f"    End   Pool: {i}")
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
    from time import time
    now = time()
    bayesian = Bayesian(0.99)
    # rejection_dict = stochastic_process_simulation(bayesian, 100000, 2000, replacement=False)
    rejection_dict = stochastic_process_simulation(bayesian, 1000, 1000, replacement=False)
    print(rejection_dict, sum(rejection_dict.values()))
    after = time()
    duration = after - now
    print(f"duration: {duration}")
    pass
