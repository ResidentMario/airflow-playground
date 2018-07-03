* Core UNIX commands are stored as ELF (the binary UNIX ABI file format) files in `/bin`. For example, `ls` is defined by `/bin/ls`.
* You can alias a command. For example on my Desktop `ls` is aliased to `ls --color=auto`.
* UNIX performs a backwards search to `/bin` through the list of folder locations specified in the `PATH` environment variable.
* A Python environment consists of a set of library files and a set of executable files.
* `conda` and `virtualenv` will append a pointer to the folder containing the binaries to the `PATH`. E.g. `/miniconda3/envs/airflow-playground/bin`.
* When `airflow scheduler` is run, the `airflow` executable in the above folder is selected and executed.
* You can recover the full path, `/home/alex/miniconda3/envs/airflow-playground/bin/airflow`, by running `which airflow`.
* Binary executables in the ELF format may be run right away. 
* All other executables must provide an interpreter hint. The interpreter hint is formatted as a shebang at the first line of the file. E.g. `#!/home/alex/miniconda3/envs/airflow-playground/bin/python`.
* UNIX expects to find an ELF at the end of this shebang, potentially with some symbolic links along the way (as occurs when using a virtual environment). That ELF is used as an interpreter to execute the file.
* Python executables included in a package are declared in `setup.py`, and written to disc during the install in a standardized way during the `pip install`. For example, here is the `airflow` executable (off a `pip install -e .` on master, hence the "incubating"):

```python
#!/home/alex/miniconda3/envs/airflow-playground/bin/python
# EASY-INSTALL-DEV-SCRIPT: 'apache-airflow==2.0.0.dev0+incubating','airflow'
__requires__ = 'apache-airflow==2.0.0.dev0+incubating'
__import__('pkg_resources').require('apache-airflow==2.0.0.dev0+incubating')
__file__ = '/home/alex/Desktop/incubator-airflow/airflow/bin/airflow'
exec(compile(open(__file__).read(), __file__, 'exec'))
```

* This file, interpreted by the requisite environment's Python binary, is what is actually hit when running `airflow [subcommand]`.
* This file reads in a file in the package (`/home/alex/Desktop/incubator-airflow/airflow/bin/airflow`), compiles it to a code object, and then executes that code object.
* Thusly the packaging ends and the user-defined code running begins.
* In Airflow, here is the contents of the file that gets hot-swapped in:

```
import os
from airflow import configuration
from airflow.bin.cli import CLIFactory

if __name__ == '__main__':

    if configuration.conf.get("core", "security") == 'kerberos':
        os.environ['KRB5CCNAME'] = configuration.conf.get('kerberos', 'ccache')
        os.environ['KRB5_KTNAME'] = configuration.conf.get('kerberos', 'keytab')

    parser = CLIFactory.get_parser()
    args = parser.parse_args()
    args.func(args)
```

* `CLIFactory.get_parser()` builds a new parser (uses `argparse`). `parser.parse_args()` gets the arguments from `sys.args`. Finally `args.func(args)` executes the code on the arguments.
* When running `airflow scheduler`, ultimately the `scheduler` routine in `bin/cli.py` is called up and ran.
* A