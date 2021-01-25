from hackathonbaobab2020.core import Instance, ZipBatch
import hackathonbaobab2020.core.tools as tools
from hackathonbaobab2020.solvers import get_solver
import zipfile
import os
import shutil
from timeit import default_timer as timer
import logging as log


def solve_zip(zip_name, path_out, path_in='data/', solver_name='default', test=False, instances=None, options=None):
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    batch_out_path = os.path.join(path_out, os.path.splitext(zip_name)[0])
    if options is None:
        options = {}
    if options.get('DEBUG', False):
        log.basicConfig(level=log.DEBUG)
    else:
        log.basicConfig(level=log.INFO)
    # we recreate the whole batch output file
    # if os.path.exists(batch_out_path):
    #     shutil.rmtree(batch_out_path)
    if not os.path.exists(batch_out_path):
        os.mkdir(batch_out_path)

    path = os.path.join(path_in, zip_name)
    zip_obj = zipfile.ZipFile(path)
    all_files = zip_obj.namelist()
    if test:
        all_files = all_files[:3]
    if instances is not None:
        all_files = instances
    solver = get_solver(solver_name)
    # for each file:
    for filename in all_files:
        # filename = all_files[0]
        experiment_dir = os.path.join(batch_out_path, filename)
        if os.path.exists(experiment_dir):
            shutil.rmtree(experiment_dir)
        os.mkdir(experiment_dir)
        data = zip_obj.read(filename)
        inst = Instance.from_mm(path=None, content=data.decode().splitlines(True))
        algo = solver(inst)
        start = timer()
        try:
            status = algo.solve(options)
        except Exception as e:
            status = 0
            with open(os.path.join(experiment_dir, 'error.txt'), 'w') as f:
                f.write(str(e))

        # export everything:
        status_conv = {4: "Optimal", 2: "Feasible", 3: "Infeasible", 0: "Unknown"}
        _log = dict(time=timer() - start, solver=solver_name, status=status_conv.get(status, "Unknown"))
        _log.update(options)
        tools.write_json(_log, os.path.join(experiment_dir, 'options.json'))
        inst.to_json(os.path.join(experiment_dir, 'input.json'))
        if algo.solution is not None:
            algo.solution.to_json(os.path.join(experiment_dir, 'output.json'))


def solve_scenarios_and_zip(scenarios, path_to_dir, solver_name, zip=False, **kwargs):
    zipfile_name = path_to_dir + '.zip'
    for scenario in scenarios:
        solve_zip(scenario, path_to_dir + '/', solver_name=solver_name, **kwargs)
    if not zip:
        return
    root_dir = 'data'
    base_dir = solver_name
    if os.path.exists(zipfile_name):
        os.remove(zipfile_name)
    shutil.make_archive(path_to_dir, 'zip', root_dir=root_dir, base_dir=base_dir)
    # shutil.rmtree(path_to_dir)


def get_table(zipfile_name):
    batch = ZipBatch(zipfile_name)
    objs = batch.get_objective_function()
    opts = batch.get_options()
    errors = batch.get_errors().vapply(lambda v: dict(errors=v))
    opts.update(errors)
    opts_df = batch.format_df(opts).drop(['instance'], axis=1)
    table = batch.format_df(objs).rename(columns={0: 'objective'}).drop(['instance'], axis=1)
    result = \
        table.merge(opts_df, on=['scenario', 'name'], how='left')
    return result


if __name__ == '__main__':
    path = 'data/'
    scenarios = ['c15.mm.zip', 'c21.mm.zip', 'j10.mm.zip', 'j30.mm.zip', 'm1.mm.zip',
                 'm5.mm.zip', 'n0.mm.zip', 'n1.mm.zip', 'n3.mm.zip', 'r1.mm.zip',
                 'r4.mm.zip', 'r5.mm.zip']
    solver_name = 'ortools'
    path_to_dir = 'data/' + solver_name
    zipfile_name = path_to_dir + '.zip'
    # solve_scenarios_and_zip(scenarios, path_to_dir, solver_name, test=True)
    get_table(zipfile_name)
