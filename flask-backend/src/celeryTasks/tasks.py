from time import sleep
from typing import Dict

from celery.exceptions import SoftTimeLimitExceeded
from flask_sse import sse

from src.ABTestSimulation.ABTestSimulation import ABTestSimulation
from src.DatabaseConnection.InsertDataset import InsertDataset
from src.extensions import celery_extension, database_connection
from src.utils.Logger import Logger
from src.utils.pathParser import getAbsPathFromProjectRoot


@celery_extension.task(name="dummy_task")
def dummy_task(user_id: str, duration: int):
    sleep(duration)
    message = f"slept {duration} seconds"
    Logger.log(message)

    sse.publish("Hello world!", type='tasktest')

    return message


@celery_extension.task(name="insert_dataset")
def insert_dataset(user_id: str, filenames: Dict[str, str], column_select_data: dict):
    print(user_id, filenames, column_select_data)

    # debug
    filenames = {"purchases.csv":getAbsPathFromProjectRoot("../datasets/h_m/purchases.csv"),"articles.csv":getAbsPathFromProjectRoot("../datasets/h_m/articles.csv"),"customers.csv":getAbsPathFromProjectRoot("../datasets/h_m/customers.csv")}
    column_select_data = {"dataset_name":"H&M","file_seperators":{"purchases.csv":",","articles.csv":",","customers.csv":","},"file_column_data_types":{"purchases.csv":{"t_dat":"date","price":"float","article_id":"Int64","customer_id":"Int64"},"articles.csv":{"article_id":"Int64"},"customers.csv":{"customer_id":"Int64"}},"purchase_data":{"filenames":["purchases.csv"],"column_name_bought_on":"t_dat","column_name_price":"price","column_name_article_id":"article_id","column_name_customer_id":"customer_id","article_metadata_attributes":[],"customer_metadata_attributes":[]},"article_metadata":[{"filenames":["articles.csv"],"column_name_id":"article_id","attributes":[{"column_name":"product_code","name":"product_code","type":"int"},{"column_name":"graphical_appearance_name","name":"graphical_appearance_name","type":"string"},{"column_name":"image_url","name":"image_url","type":"image"}]}],"customer_metadata":[{"filenames":["customers.csv"],"column_name_id":"customer_id","attributes":[{"column_name":"age","name":"age","type":"float"},{"column_name":"postal_code","name":"postal_code","type":"string"}]}]}

    insert_dataset_obj = InsertDataset(database_connection, user_id, filenames, column_select_data)

    try:
        insert_dataset_obj.start_insert()

    except ValueError as err:
        insert_dataset_obj.abort()
        Logger.logError(str(err))
        raise err

    except Exception as err:
        insert_dataset_obj.abort()
        Logger.logError(str(err))
        raise err

    finally:
        insert_dataset_obj.cleanup()

    return "started dataset insert"


@celery_extension.task(name="start_simulation")
def start_simulation(user_id: str, simulation_input: dict):
    simulation = ABTestSimulation(database_connection, sse, simulation_input)
    simulation.run()

    return "started simulation"
