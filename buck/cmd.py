import argparse
import configparser
import copy
import os
import subprocess

from jinja2 import Environment, FileSystemLoader, select_autoescape

__THIS__ = os.path.dirname(os.path.abspath(__file__))

KNOWN_FILES = [
    # relative to the toplevel directory of the git repo.
    ('src/config.yaml.j2', 'src/config.yaml'),
    ('.zuul.yaml.j2', '.zuul.yaml'),
]

OPENSTACK_INFO = {
    'origin': 'zed'
}


def read_gitreview():
    cwd = os.getcwd()
    gitreview_path = os.path.join(cwd, '.gitreview')
    if not os.path.isfile(gitreview_path):
        return None

    config = configparser.ConfigParser()
    config.read(gitreview_path)
    return config


def setup_opts():
    parser = argparse.ArgumentParser(description='buck automation.')
    subparsers = parser.add_subparsers(title='subcommands', required=True,
                                       dest='cmd')
    up = subparsers.add_parser('up')
    up.set_defaults(func=cmd_up)

    return parser.parse_args()


def cmd_up(args):
    cwd = os.getcwd()
    env = Environment(
        loader=FileSystemLoader([cwd, os.path.join(__THIS__, 'templates')]),
        autoescape=select_autoescape()
    )
    print('CWD', cwd)
    for in_file, out_file in KNOWN_FILES:

        result = subprocess.run(['git', 'ls-files', '--error-unmatch',
                                 os.path.join(cwd, out_file)], check=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        if result.returncode == 0:
            # the file is tracked by git, so we skip overriding it.
            print(f'Skipping {out_file}, reason: tracked by git')
            continue

        print(f'Using {in_file} template')
        template = env.get_template(in_file)

        os_info = copy.deepcopy(OPENSTACK_INFO)
        gitreview = read_gitreview()
        try:
            os_info['origin'] = gitreview['gerrit']['defaultbranch'].split('/')[-1]
        except:
            raise
        result = template.stream({'openstack': os_info,
                                  'gitreview': gitreview})

        print(f'Writing {out_file}...', end='')
        with open(out_file, 'w') as f:
            result.dump(f)
            f.write('\n')
        print('done')


def main():
    args = setup_opts()
    args.func(args)
