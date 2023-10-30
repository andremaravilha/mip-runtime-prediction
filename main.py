import os
import datetime
import json
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import RLock
import gurobipy as gp
from gurobipy import GRB


# Some global objects
global lock
lock = RLock()


# MIPLIB2017 instance filter
def filter_miplib2017(instance):

    # Only easy instances are considered
    if instance['status'] in ['open', 'hard']:
        return False

    # Only instances with a known optimal solution are considered
    if instance['is_infeasible'] or instance['is_unbounded'] or not instance['is_optimal']:
        return False
    
    # Only MIP instances are considered
    if instance['size']['binaries']['original'] + instance['size']['integers']['original'] < 1:
        return False
    
    # tags:
    # 'aggregations', 'benchmark', 'benchmark_suitable', 'binary', 
    # 'binpacking', 'cardinality', 'decomposition', 'equation_knapsack', 
    # 'feasibility', 'general_linear', 'indicator', 'infeasible', 
    # 'integer_knapsack', 'invariant_knapsack', 'knapsack', 'mixed_binary', 
    # 'no_solution', 'numerics', 'precedence', 'set_covering', 'set_packing', 
    # 'set_partitioning', 'variable_bound'
    forbidden_tags = {'decomposition', 'feasibility', 'indicator', 'infeasible', 'no_solution', 'numerics'}
    if instance['tags'] is not None and len(instance['tags']) > 0:
        for tag in instance['tags']:
            if tag in forbidden_tags:
                return False
    
    return True


# Auxiliary function to get a value or its default
def get_value(o, keys, default):
    success = True
    for k in keys:
        if o is not None:
            o = o.get(k, None)
        else:
            success = False
            break
    return o if success else default


# Get instance features
def get_instance_features(instance):
    return map(lambda x: str(x), 
               [instance['objective'],
                instance['size']['variables']['original'],
                instance['size']['binaries']['original'],
                instance['size']['integers']['original'],
                instance['size']['continuous']['original'],
                instance['size']['constraints']['original'],
                instance['size']['nonzero_density']['original'],
                get_value(instance, ['constraints', 'empty', 'original'], 0),
                get_value(instance, ['constraints', 'free', 'original'], 0),
                get_value(instance, ['constraints', 'singleton', 'original'], 0),
                get_value(instance, ['constraints', 'aggregations', 'original'], 0),
                get_value(instance, ['constraints', 'precedence', 'original'], 0),
                get_value(instance, ['constraints', 'variable_bound', 'original'], 0),
                get_value(instance, ['constraints', 'set_partitioning', 'original'], 0),
                get_value(instance, ['constraints', 'set_packing', 'original'], 0),
                get_value(instance, ['constraints', 'set_covering', 'original'], 0),
                get_value(instance, ['constraints', 'bin_packing', 'original'], 0),
                get_value(instance, ['constraints', 'knapsack', 'original'], 0),
                get_value(instance, ['constraints', 'integer_knapsack', 'original'], 0),
                get_value(instance, ['constraints', 'cardinality', 'original'], 0),
                get_value(instance, ['constraints', 'invariant_knapsack', 'original'], 0),
                get_value(instance, ['constraints', 'equation_knapsack', 'original'], 0),
                get_value(instance, ['constraints', 'mixed_binary', 'original'], 0),
                get_value(instance, ['constraints', 'general_linear', 'original'], 0)])


# Function to run Gurobi solver in a subprocess
def run_gurobi_solver(instance, seed, output_file):
    global lock
    status = 'unknown'
    runtime = ''
    nodes = ''
    objective = ''

    try:

        # Download the instance
        filename = os.path.join('data', 'instances', f'{instance["name"]}.mps.gz')
        #filename = os.path.join('data', 'instances', f'{instance["name"]}.mps')
        if not os.path.exists(filename):
            urllib.request.urlretrieve(instance['url_download'], filename=filename)

        # Load the instance
        gp.setParam('OutputFlag', 1)
        gp.setParam('LogToConsole', 0)

        model = gp.read(filename)
        model.setParam('Threads', 1)
        model.setParam('Seed', seed)
        #model.setParam('TimeLimit', 3600)
        model.setParam('LogFile', 
                       os.path.join('data', 'gurobi_log', 
                                      f'{instance["name"]}_{seed}_{datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")}.log'))

        # Solve the instance
        model.optimize()
    
        # Get the results
        runtime = model.Runtime
        nodes = model.NodeCount
        if model.SolCount > 0:
            objective = model.ObjVal
            if model.Status == GRB.OPTIMAL:
                status = 'optimal'
            else:
                status = 'feasible'
        else:
            if model.Status == GRB.INF_OR_UNBD:
                status = 'infeasible_or_unbounded'
            elif model.Status == GRB.INFEASIBLE:
                status = 'infeasible'
            elif model.Status == GRB.UNBOUNDED:
                status = 'unbounded'

    except Exception as e:
        print(f'Error while solving instance [ instance: {instance["name"]}, seed: {seed} ]: {e}')
        status = 'error'
        runtime = ''
        nodes = ''
        objective = ''
    
    # Write the results to the output file
    with lock:
        try: 
            with open(output_file, 'a') as f:
                line = f'{instance["name"]},{seed},{status},{objective},{nodes},{runtime},' + ','.join(get_instance_features(instance)) + '\n'
                f.write(line)
        except Exception as e:
            print(f'Error while writing results [ instance: {instance["name"]}, seed: {seed} ]: {e}')


# Run the computational experiments
def main():

    workers = 3
    output_file = os.path.join('data', 'results.csv')
    seeds = [0]
    
    # Load a list of selected instances from MIPLIB2017
    instances = dict()
    with open(os.path.join('data', 'miplib2017.json')) as f:
        miplib = json.load(f)
        for instance in miplib:
            if filter_miplib2017(instance):
                instances[instance['name']] = instance    

    # Create and initialize the output file
    if not os.path.exists(output_file):
        with open(output_file, 'w') as f:
            columns = ['instance', 'seed', 'opt.status', 'opt.obj', 'opt.nodes', 'opt.runtime', 
                       'optimal', 'var.size', 'var.binaries', 'var.integers', 'var.continuous', 
                       'constr.size', 'const.density', 'constr.empty', 'constr.free', 'constr.singleton',
                       'constr.aggregation', 'constr.precedence', 'constr.variable_bound', 'constr.set_partitioning',
                       'constr.set_packing', 'constr.set_covering', 'constr.binpacking', 'constr.knapsack', 
                       'constr.integer_knapsack', 'constr.cardinality', 'constr.invariant_knapsack', 
                       'constr.equation_knapsack', 'constr.mixed_binary', 'constr.general_linear']
            f.write(','.join(columns) + '\n')
    
    # Check entries (i.e., pairs of instance and seed) already solved
    solved_entries = []
    with open(output_file, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:
            columns = line.split(',')
            if columns[2] not in ['unknown', 'error', '']:
                solved_entries.append( (columns[0], int(columns[1])) )
    
    # Run unsolved entries (i.e., pairs of instance and seed)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for seed in seeds:
            for key in instances.keys():
                instance = instances[key]
                if (instance['name'], seed) not in solved_entries:
                    executor.submit(run_gurobi_solver, instance, seed, output_file)


if __name__ == '__main__':
    main()
