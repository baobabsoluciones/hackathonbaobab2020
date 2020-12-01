from core import Instance, Experiment, ZipBatch
import zipfile
import os
from solvers import get_solver
import shutil


def solve_zip(zip_name, path_out, path_in='data/', solver_name='default'):
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
    solver = get_solver(solver_name)
    # for each file:
    for filename in all_files:
    # filename = all_files[0]
        experiment_dir = os.path.join(batch_out_path, filename)
        os.mkdir(experiment_dir)
        data = zip_obj.read(filename)
        inst = Instance.from_mm(path=None, content=data.decode().splitlines(True))
        algo = solver(inst)
        try:
            finished = algo.solve({})
        except Exception as e:
            with open(experiment_dir + 'error.txt', 'w') as f:
                f.write(str(e))

        # export everything:
        inst.to_json(os.path.join(experiment_dir, 'input.json'))
        if algo.solution is not None:
            algo.solution.to_json(os.path.join(experiment_dir, 'output.json'))

    # TODO: maybe zip at the end once per solver
    root_dir, base_dir = os.path.split(batch_out_path)
    shutil.make_archive(batch_out_path, 'zip', root_dir=root_dir, base_dir=base_dir)
    shutil.rmtree(batch_out_path)

def get_statistics(path):
        zipfiles = [os.path.join(path, file) for file in os.listdir(path)]
        for zf in zipfiles:
            batch = ZipBatch(zf, no_scenario=True)
            batch.get_objective_function()
            batch.get_errors()


if __name__ == '__main__':
    path = 'data/'
    scenarios = ['c15.mm.zip', 'c21.mm.zip', 'j10.mm.zip', 'j30.mm.zip', 'm1.mm.zip', 'm5.mm.zip', 'n0.mm.zip', 'n1.mm.zip', 'n3.mm.zip', 'r1.mm.zip', 'r4.mm.zip', 'r5.mm.zip']
    solver_name = 'default'
    path_to_dir = 'data/' + solver_name
    for scenario in scenarios:
        solve_zip(scenario, path_to_dir + '/', solver_name=solver_name)
    # root_dir = 'data'
    # base_dir = solver_name
    # zipfile_name = path_to_dir + '.zip'
    # os.remove(zipfile_name)
    # shutil.make_archive(path_to_dir, 'zip', root_dir=root_dir, base_dir=base_dir)


    # for scenario in scenarios:
    #     batch = ZipBatch(path_to_dir + '/' + scenario, no_scenario=True)
    #     batch.get_objective_function()
    #     batch.get_errors()
    # exps = batch.list_experiments()
    # batch.get_instances_paths()
