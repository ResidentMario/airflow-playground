from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'abilogur@',
    'start_date': datetime(2018, 7, 3),
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}


dag = DAG('BashOperatorDAG', default_args=default_args, schedule_interval=timedelta(days=1))
task = BashOperator(task_id='print_date', bash_command='date >> ~/Desktop/airflow-playground/date.txt', dag=dag)
