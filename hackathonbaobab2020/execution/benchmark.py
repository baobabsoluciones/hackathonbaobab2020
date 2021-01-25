from run_batch import solve_scenarios_and_zip, solve_zip, get_table
import zipfile
import random as rn
import os
import shutil
import pandas as pd


def sample_instances(scenario_file, n=5):
    zip_obj = zipfile.ZipFile(scenario_file)
    instances = zip_obj.namelist()
    return rn.sample(instances, n)


sampled_instances = \
    {'c15.mm.zip': ['c1555_1.mm', 'c1530_5.mm', 'c1528_7.mm', 'c1562_2.mm', 'c1522_4.mm'], 'c21.mm.zip': ['c2134_10.mm', 'c2131_4.mm', 'c2114_3.mm', 'c2149_6.mm', 'c2158_6.mm'], 'j10.mm.zip': ['j1051_7.mm', 'j1014_3.mm', 'j1043_5.mm', 'j1051_2.mm', 'j1027_10.mm'], 'j30.mm.zip': ['j309_5.mm', 'j3023_1.mm', 'j3023_7.mm', 'j3021_9.mm', 'j3039_6.mm'], 'm1.mm.zip': ['m153_2.mm', 'm15_10.mm', 'm135_3.mm', 'm152_1.mm', 'm145_9.mm'], 'm5.mm.zip': ['m537_4.mm', 'm559_9.mm', 'm528_6.mm', 'm526_9.mm', 'm546_4.mm'], 'n0.mm.zip': ['n039_9.mm', 'n029_2.mm', 'n045_7.mm', 'n010_8.mm', 'n02_4.mm'], 'n1.mm.zip': ['n124_2.mm', 'n110_4.mm', 'n11_1.mm', 'n120_1.mm', 'n163_2.mm'], 'n3.mm.zip': ['n331_5.mm', 'n362_5.mm', 'n313_2.mm', 'n33_10.mm', 'n352_9.mm'], 'r1.mm.zip': ['r140_6.mm', 'r132_7.mm', 'r125_5.mm', 'r135_1.mm', 'r145_2.mm'], 'r4.mm.zip': ['r461_4.mm', 'r424_8.mm', 'r463_1.mm', 'r422_7.mm', 'r448_5.mm'], 'r5.mm.zip': ['r534_9.mm', 'r519_5.mm', 'r539_6.mm', 'r538_8.mm', 'r525_9.mm']}
path = 'data/'
scenarios = ['c15.mm.zip', 'c21.mm.zip', 'j10.mm.zip', 'j30.mm.zip', 'm1.mm.zip',
             'm5.mm.zip', 'n0.mm.zip', 'n1.mm.zip', 'n3.mm.zip', 'r1.mm.zip',
             'r4.mm.zip', 'r5.mm.zip']
solvers = ['default', 'ortools', 'Iterator_HL', 'loop_EJ']
root_dir = 'benchmark'

def solve_all():

    # TODO: take this out
    scenarios = ['c15.mm.zip']
    # solvers = ['default']
    # TODO taje out above

    options = dict(timeLimit=300, DEBUG=False)
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir)
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

    for solver in solvers:
        path_out = '{}/{}'.format(root_dir, solver)
        path_to_dir = path_out
        path_in = path
        solver_name = solver
        zipfile_name = path_to_dir + '.zip'
        for scenario in scenarios:
            solve_zip(scenario, path_to_dir + '/', solver_name=solver_name,
                      instances=sampled_instances[scenario], options=options)
        base_dir = solver_name
        if os.path.exists(zipfile_name):
            os.remove(zipfile_name)
        shutil.make_archive(path_to_dir, 'zip', root_dir=root_dir, base_dir=base_dir)


def compare():
    table = pd.concat([get_table('{}/{}'.format(root_dir, solver)) for solver in solvers])
    table.to_csv('{}/{}'.format(root_dir, 'summary.csv'), index=False)
    print(table.to_markdown())

if __name__ == '__main__':
    # solve_all()
    table = compare()

    pass