### File structure and configuration

* Airflow installs in two file locations.
* The Python package, which defines the actual executable and the command line interface, is installed wherever your environment manager places your packages.
* Configuration variables live in a file named `airflow.cfg` in `$AIRFLOW_HOME`, if that environment variable was specified at `pip install` time, or `~/airflow`, if it was not.
* h
* The list of DAGs that you can run live in the same folder, in the `/dags` subdirectory.
  * This behavior can be changed by editing the `dags_folder` configuration variable.
  * Since DAG discovery is shared across every installed `airflow` package, this seems to be of limited use. If you have `project1` and `project2`, both using `airflow`, there isn't a more natural place for their DAGs than `~/airflow` or a similar unified directory, due to this shared concern.
* `$AIRFLOW_HOME` also contains `airflow.db`, a `sqlite3` file and the backing store for Airflow operations.
  * This backing store is only sufficient for sequential operation. You are expected to outgrow it, and to need to move to a separate Postgres process.
* The webserver will emit its PID to `$AIRFLOW_HOME/airflow-webserver.pid` at runtime.


* By default all commands you run will include a long list of built-in "tutorial" DAGs. To get rid of them you have to set `load_examples = False` in the config file.
  * If you have already run the Airflow web client once, the example DAGs will populate durably in the database, and setting this config variable will not be enough; you will need to also go and run `airflow resetdb`.
  * Note that this command is a full database reset. All historical information will be gone.
  * IMPROVEMENT: Add a "Hide Example DAGs" button to the interface, will will hide the example DAGs in the webservice only.


* When upgrading `airflow`, without making any changes to configuration pointers, it will use the pre-existing configuration files.
  * This will likely result in an error at scheduler launch time (see the next section for what the scheduler is) due to database incompatibility.
  * You need to additionally perform a `resetdb` operation to migrate the database.


### Basic operations
* DAGs are run by a scheduler process. You launch the scheduler with `airflow scheduler`.
* There is a web client that you can launch with `airflow webserver`. The web client is a good way of interacting with DAGs.
* You can perform most of the actions you can perform from the CLI in the web client, plut you get some nice visualizations.
* Airflow does not gracefully handle webserver DAG starts that occur in the absence of a webserver. If you try to run a DAG without a scheduler up you will find yourself stuck at the "Running" state for all eternity.
  * It seems that triggering a DAG run populates an entry in the database, but no verification is done as to whether or not that DAG run can or will actually execute!
  * IMPROVEMENT: warn the user when launching a manual DAG run without a schedule processor alive.
* Things you can do with a DAG are organized as a series of links:
  * Trigger DAG will kick of a manual DAG run.
  * Tree View will provide a DAG tree view, folded in with an execution timeline.
  * Graph View provides a better tree visualization.
  * Task Duration does...something? Come back to this.
  * Task Tries does...something? Come back to this.
  * Landing Times?
  * Gantt?
  * Code View shows you the latest version of the DAG code.
    * No historical view for old versions of the DAG definition!
  * Logs provides a filterable view of logged events. Logged events include DAG task executions (no information on success or failure, however), web page access details (worthless clutter), some other small stuff (e.g. pauses).
* IMPROVEMENT: the link to the documentation in the web UI is outdated, and leads to a 404.


* You can pause and unpause a DAG in the top level view. This will not affect runs that are already enqueued, but will prevent any further runs from being queued.

### Task argument
* When creating a DAG you pass a list of arguments to the task creator. For example, here are the arguments passed in the tutorial example:

```python
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2018, 6, 30),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}
```

* These parametrize the `DAG` object, which passes them to the `airflow.models.BaseOperator`, which is the object class that all other operators inherit from. You can also specify these parameters on the operators directly, for more fine-grained control. The [documentation entry](https://airflow.apache.org/code.html#airflow.models.BaseOperator) on this class is informative reading. A summary:
  * owner &mdash; Task owner; the document recommends using the "Unix username", but probably an LDAP would be better.
  * retries, retry_delay, retry_exponential_backoff, max_retry_delay &mdash; Configures retry behavior. 0 means no retries.
  * start_date &mdash; A toughie. `min(start_date)` across all tasks in a DAG run is the time that a DAG run is first run.
  * schedule_interval &mdash; The interval in between DAG or task runs. 
  * end_date &mdash; The last time a DAG run occurs, if specified.
  * depends_on_past &mdash; The DAG run will only start after (sequentially) waiting for a success code from the immediately prior DAG run.
  * wait_for_downstream &mdash; Task will wait for all operations downstream of the previous instance of the task to succeed before doing anything.
  * queue &mdash; If using the celery executor, where to enqueue the job.
  * priority_weight &mdash; Execution order weighting for high load times.
  * pool &mdash; The concurrent pool that the task is assigned to. Used to limit concurrency.
  * sla &mdash; Time by which the job is expected to succeed. SLA misses are logged in a specific part of the UI.
  * execution_timeout &mdash; Hard max time. Tasks that exceed this time will be forcefully stopped.
  * on_failure_callback, on_retry_callback, on_success_callback &mdash; Tin.
  * trigger_rule &mdash; Configured predacessor success rules. By default you need all predacessor tasks to succeed, but you can also specify any one success or other things.
  * resources, run_as_user, task_concurrency &mdash: IDK I do not understand these.
  
### Setting up a backend

* The default SQLite backend has rate limitations and should not be used in production.
* Instead you should use any of the supported databases. All databases supposed by SQLAlchemy work (that's most of them).
* Here's a sequence of commands for getting a Postgres backing store up and running:

```bash
mkdir ~/postgres
pg_ctl -D /Users/alex/postgres -l logfile start
createdb airflow
airflow initdb
```

* You then need to change the following two config lines in `airflow.cfg`:

```bash
executor = LocalExecutor     
sql_alchemy_conn = postgresql+psycopg2://localhost/airflow
```

### Concepts
* DAG operators must be scoped at the top of the file. They cannot be hidden within closures, e.g. functions.
* DAG default arguments get passed to operators. You can further modify operators at their definition. 
* Some things make more sense in the context of the whole DAG, others only in the operator. Some could live in either place.
* An operator may be instantiated with run-time **variables**.
* Variables have global scope to all running tasks. They may be defined and manipulated using any of the CLI, code calls, and the UI.
* They're basically a shared key-value store used for configuration variables.
* An instantiated operator is a **task**.
* A **task instance** is a specific run of a task. Since tasks occur within the frame of DAGs, task instances may be defined as a tuple of {DAG, Task, Timestamp}.
* A task itself is an {Operator, Instance Variables} tuple.
* **Pools** may be used to limit parallelism.
  * Pools are a {name, number of worker slots} concept.
  * If the amount of jobs submitted to a pool exceeds the number of slots in the pool, a priority queue will be formed.
  * The priority of a task instance is the sum of its priority and that of all downstream tasks.
  * You can manage pools via `Menu -> Admin -> Pools`.
* **Hooks** define connections to external systems like e.g. Apache Pig. They abstract authentication information and similar concerns out of the pipelines.
  * Hooks are a low-level concept that is used to build operators, the corresponding higher-level object.
  * **Connections** define all of the metadata necessary for a specific connecting system.
  * Connection information is stored in the Airflow metadata database and may be managed via the UI.  
  * Hooks define a `get_connection` method. Operators use hooks to link to external resources using this method.
  * Every connection has a `conn_id`. Multiple connections having the same `conn_id` may be defined.
  * In the presence of multiple connections with the same `conn_id`, a hook will randomly choose one connection as its target. This allows rudimentary load balancing.
  * In addition to management within Airflow, you can manage connection IDs using OS variables.
  * An OS variable `AIRFLOW_CONN_POSTGRES_MASTER` will define a connection variable `postgres_master` within Airflow.
  * Pers note: I immediately gravitate towards using OS variables for managing this metadata! It makes more sense in a container context. Style decision.
* Queues : TODO
* XComs
  * XComs are a intertask data sharing scheme.
  * They use Pickle serialization.
  * Avoid using until absolutely necessary! Tasks should be atomic and self-contained as much as possible.
* Branching paths (execute this, not that) are possible using a `BranchPythonOperator`. This is a "magic" operator that is supposed to return the `task_id` that is next to be run.
* SubDAGs can be implemented, if you need reusable components in your graph.
  * A common pattern for sub-DAGs is to have them scoped to a function. This prevents their being populated as their own separate DAG in the interface.
  * SubDAGs follow what AirBnB calls the "stage-check-exchange pattern": they are built in a test area, checked for issues, then swapped into the production area. Cute.
* **Service-level agreements** may be set up, with email scheduling and a Missed SLAs view available for analysis.
* Trigger rules are a thing.
* Zombies and undead processes. Oh boy!
  * On UNIX a **zombie process** is one that has completed execution, yet still has an entry in the process table.
  * In Airflow zombie processes occur when the task instance has completed (and hence no longer emits a heartbeat), but still has a "Running" populated in the metadata store.
     * This typically occurs due to network partitions or ungraceful shutdowns. 
     * The scheduler periodically performs zombie strike-downs as part of its normal operations. 
  * Undead processes have a heartbeat but no entry in the metadata store (this is akin to an orphan process in UNIX).
     * Undead processes can happen due to scheduler restarts and related faults?
     * The task instance will get a "wut" ack from the scheduler when it goes to register a heartbeat, and will know to stop.
* Question: what happens if a task heartbeats the scheduler, but times out?
* A **cluster policy** can be set that conforms DAGs and tasks to desired "admin-set" properties (TODO: dive into what you can control with these properties).
* You can attach documentation to your tasks using special `doc_md` (and friends) attributes. These will be rendered in the UI.
* Jinja templating may be used to parametrize operators in the file definition.
  * The templates will be evaluated at runtime.
  * This is just a convenient, for certain use cases, alternative to specifying things using raw Python.
  * Particularly Jinja macros can be very useful.

### Data profiling
* Airflow includes a data profiling page. This allows you to write SQL queries, download CSVs from SQL queries, and draw graphs on-screen. Just like a SQL Explorer.
* Cute. Description: https://airflow.apache.org/profiling.html.


### Scheduling and triggers
* Tasks that are scheduled are run at the end of the `schedule_interval` wait period, not before.
* Airflow makes no guarantees as to exactness of a run time. Tasks are scheduled "soon" after their designated time, but never before.
* `schedule_interval` may be either a chron expression or a timedelta object.
* By default all DAG runs in the past that have not been run yet will be scheduled. This is known as a **catchup**.
* You can turn this behavior off obviously.
* It's also possible to run a DAG within a specified time interval manually. This is a **backfill** (particularly useful when developing).
* You can also run a `trigger_dag` on either the CLI or through the UI. The run's timestamp is the trigger timestamp.
* How do you unblock tasks?
  * You can clear runs from the UI. Removing them from the history in this way will cause a catchup to run on them, if applicable.
  * You can also this via `airflow clear -h` in the UI.
  * Clearing a task instance doesn't delete the old task information. Instead it raises `max_tries` by one, and sets the current task instance state to `None`.
  * You can manually mark a task instance as a success via the UI. This can be used to fix false negatives and such.