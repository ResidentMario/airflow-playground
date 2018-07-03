from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os

default_args = {
    'owner': 'abilogur@',
    'start_date': datetime(2018, 7, 3),
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}


def python_callable():
    with open(os.path.abspath(".") + "/date.txt", "w") as f:
        f.write(str(datetime.now()))


dag = DAG('PythonOperatorDAG', default_args=default_args, schedule_interval=timedelta(days=1))
task = PythonOperator(task_id='print_date', python_callable=python_callable, dag=dag)
