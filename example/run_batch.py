from core import Instance, Experiment, ZipBatch
import zipfile
import os
from solvers import get_solver
import shutil
from timeit import default_timer as timer
import core.tools as tools


def solve_zip(zip_name, path_out, path_in='data/', solver_name='default', test=False):
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    batch_out_path = os.path.join(path_out, os.path.splitext(zip_name)[0])

    # we recreate the whole batch output file
    if os.path.exists(batch_out_path):
        shutil.rmtree(batch_out_path)

    os.mkdir(batch_out_path)

    path = os.path.join(path_in, zip_name)
    zip_obj = zipfile.ZipFile(path)
    all_files = zip_obj.namelist()
    if test:
        all_files = all_files[:3]
    solver = get_solver(solver_name)
    # for each file:
    for filename in all_files:
    # filename = all_files[0]
        experiment_dir = os.path.join(batch_out_path, filename)
        os.mkdir(experiment_dir)
        data = zip_obj.read(filename)
        inst = Instance.from_mm(path=None, content=data.decode().splitlines(True))
        algo = solver(inst)
        start = timer()
        try:
            finished = algo.solve({})
        except Exception as e:
            with open(experiment_dir + 'error.txt', 'w') as f:
                f.write(str(e))

        # export everything:
        log = dict(time=timer() - start, solver=solver_name)
        tools.write_json(log, os.path.join(experiment_dir, 'options.json'))
        inst.to_json(os.path.join(experiment_dir, 'input.json'))
        if algo.solution is not None:
            algo.solution.to_json(os.path.join(experiment_dir, 'output.json'))


def get_statistics(path):
        zipfiles = [os.path.join(path, file) for file in os.listdir(path)]
        for zf in zipfiles:
            batch = ZipBatch(zf, no_scenario=True)
            batch.get_objective_function()
            batch.get_errors()


def solve_scenarios_and_zip(scenarios, path_to_dir, solver_name, **kwargs):
    for scenario in scenarios:
        solve_zip(scenario, path_to_dir + '/', solver_name=solver_name, **kwargs)

    root_dir = 'data'
    base_dir = solver_name
    if os.path.exists(zipfile_name):
        os.remove(zipfile_name)
    shutil.make_archive(path_to_dir, 'zip', root_dir=root_dir, base_dir=base_dir)


def get_table(zipfile_name):
    batch = ZipBatch(zipfile_name)
    objs = batch.get_objective_function()
    opts = batch.get_options()
    opts_df = batch.format_df(opts).drop(['instance'], axis=1)
    table = batch.format_df(objs).rename(columns={0: 'objective'}).drop(['instance'], axis=1)

    table_errors = batch.get_errors_df().drop(['instance'], axis=1)
    result = \
        table.\
        merge(table_errors, on=['scenario', 'name'], how='left').\
        merge(opts_df, on=['scenario', 'name'], how='left')
    return result


if __name__ == '__main__':
    path = 'data/'
    scenarios = ['c15.mm.zip', 'c21.mm.zip', 'j10.mm.zip', 'j30.mm.zip', 'm1.mm.zip', 'm5.mm.zip', 'n0.mm.zip', 'n1.mm.zip', 'n3.mm.zip', 'r1.mm.zip', 'r4.mm.zip', 'r5.mm.zip']
    solver_name = 'default'
    path_to_dir = 'data/' + solver_name
    zipfile_name = path_to_dir + '.zip'
    solve_scenarios_and_zip(scenarios, path_to_dir, solver_name, test=True)
    get_table(zipfile_name)
