import math
import time
import warnings
from io import StringIO
from pathlib import Path
from typing import List

import pandas as pd
import sqlalchemy
from sqlalchemy import MetaData, exc as sa_exc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import scoped_session, sessionmaker

from Logger import Logger
from config import configDatabase


class DatabaseConnection:
    def __init__(self):
        self.engine = None
        self.session = None
        self.meta_data = None

    def connect(self, filename='database.ini', section='postgresql'):
        # read connection parameters
        params = configDatabase(filename, section)

        self.engine = sqlalchemy.create_engine(f"postgresql://{params['user']}@localHost:5432/{params['dbname']}",
                                               executemany_mode='batch')
        self.session = scoped_session(sessionmaker(bind=self.engine))
        self.meta_data = MetaData(bind=self.engine)

    def getConnection(self):
        return self.engine.connect()

    def logVersion(self):
        """
        Displays the PostgreSQL database server version
        :return: None
        """
        db_version = self.session.execute("SELECT version()").fetchone()[0]
        Logger.log("PostgreSQL database version:" + db_version)

    def queryTable(self, table, query_data: dict):
        return self.session.query(table).filter_by(**query_data)

    def insertRow(self, table, values: dict):
        self.engine.execute(table.insert(), [values])

    def insertRows(self, table, values: List[dict]):
        self.engine.execute(table.insert(), values)

    def insertRowNoConflict(self, table, values: dict):
        self.engine.execute(insert(table).values([values]).on_conflict_do_nothing())

    def insertRowsNoConflict(self, table, values: List[dict]):
        self.engine.execute(insert(table).values(values).on_conflict_do_nothing())

    def addDataset(self, dataset_name: str, uploader_name: str, purchase_data_filename: str, article_data_filename: str,
                   customer_data_filename: str):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)
            self.meta_data.reflect()

        Logger.log(f"Adding dataset {dataset_name}")

        # add row in dataset table
        if not self.__addDatasetEntry(dataset_name, uploader_name):
            return False

        # check if files exist
        for filename in [purchase_data_filename, article_data_filename, customer_data_filename]:
            file = Path(filename)
            if not file.is_file():
                Logger.logError(f"Could not find {filename}")

        # execution time measurement
        start_time = time.time()

        # add rows in article table and article_attribute table
        self.__addMetaDataset(dataset_name, article_data_filename, "article")
        # add rows in customer table and customer_attribute table
        self.__addMetaDataset(dataset_name, customer_data_filename, "customer")

        # add rows in purchase table
        self.__addPurchasesDataset(dataset_name, purchase_data_filename)

        self.session.commit()

        duration = time.time() - start_time
        Logger.log(
            f"Added dataset \"{dataset_name}\" in {math.floor(duration)} seconds")

    def __addDatasetEntry(self, dataset_name: str, uploader_name: str):
        datasets_table = self.meta_data.tables["dataset"]

        # check if dataset_name already exists
        if self.queryTable(datasets_table, {"name": dataset_name}).first():
            Logger.logError(f"Couldn't add dataset {dataset_name}, it already exists")
            return False

        self.insertRow(datasets_table, {
            "name": dataset_name,
            "uploaded_by": uploader_name
        })

        return True

    def __addMetaDataset(self, dataset_name: str, meta_data_filename: str, meta_data_type: str):
        self.meta_data.reflect()
        cursor = self.session.connection().connection.cursor()

        # todo add support for custom seperator and custom index column
        df_csv = pd.read_csv(meta_data_filename, sep=',')

        attribute_names = list(df_csv)

        # check if meta_data_id atribute exists
        if meta_data_type + "_id" not in attribute_names:
            Logger.logError(f"Could not find \"{meta_data_type}_id\" column in {dataset_name}")
            return False

        df_meta_data_table = df_csv[[meta_data_type + "_id"]].copy()
        df_meta_data_table["dataset_name"] = dataset_name

        output = StringIO()
        df_meta_data_table.to_csv(output, sep='\t', header=False, encoding="utf8", index=False)
        output.seek(0)

        cursor.copy_from(output, meta_data_type, sep='\t', null='')

        for attribute_name in attribute_names:
            if attribute_name == meta_data_type + "_id":
                continue

            df_meta_data_attribute_table = df_csv[[meta_data_type + "_id"]].copy()
            df_meta_data_attribute_table["dataset_name"] = dataset_name
            df_meta_data_attribute_table["attribute"] = attribute_name
            df_meta_data_attribute_table["value"] = df_csv[attribute_name].copy()
            # todo add user defined custom type
            df_meta_data_attribute_table["type"] = 0

            # drops all rows with a null entry
            df_meta_data_attribute_table = df_meta_data_attribute_table.dropna(how="any", axis=0)

            output = StringIO()
            df_meta_data_attribute_table.to_csv(output, sep='\t', header=False, encoding="utf8", index=False)
            output.seek(0)

            cursor.copy_from(output, meta_data_type + "_attribute", sep='\t', null='',
                             columns=list(df_meta_data_attribute_table))

        return True

    def __addPurchasesDataset(self, dataset_name: str, purchases_data_filename: str):
        self.meta_data.reflect()
        cursor = self.session.connection().connection.cursor()

        # todo add support for custom seperator and custom index column
        df_purchase_data_table = pd.read_csv(purchases_data_filename, sep=',')

        attribute_names = list(df_purchase_data_table)

        # todo variable names for purchase attritubes
        # check if purchase atributes exists
        if "customer_id" not in attribute_names:
            Logger.logError(f"Could not find \"customer_id\" column in {dataset_name}")
            return False
        elif "article_id" not in attribute_names:
            Logger.logError(f"Could not find \"article_id\" column in {dataset_name}")
            return False
        elif "price" not in attribute_names:
            Logger.logError(f"Could not find \"price\" column in {dataset_name}")
            return False
        elif "t_dat" not in attribute_names:
            Logger.logError(f"Could not find \"t_dat\" column in {dataset_name}")
            return False

        df_purchase_data_table["dataset_name"] = dataset_name

        df_purchase_data_table.rename(columns={"t_dat": "timestamp"}, inplace=True)

        # drop duplicates but keep the first
        df_purchase_data_table.drop_duplicates(subset=["dataset_name", "customer_id", "article_id", "timestamp"],
                                               inplace=True)

        output = StringIO()
        df_purchase_data_table.to_csv(output, sep='\t', header=False, encoding="utf8", index=False)
        output.seek(0)

        cursor.copy_from(output, "purchase", sep='\t', null='', columns=list(df_purchase_data_table))

        return True


if __name__ == '__main__':
    db_con = DatabaseConnection()
    db_con.connect(filename="config/database.ini")
    db_con.logVersion()
    db_con.addDataset("H_M", "mosh", "../datasets/H_M/purchases.csv", "../datasets/H_M/articles.csv",
                      "../datasets/H_M/customers.csv")
