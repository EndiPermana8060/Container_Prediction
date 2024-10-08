import mysql.connector
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import constant
import os

load_dotenv()
columns_for_processing = constant.for_processing

class Processor:
    def __init__(self):
        self.username = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')
        self.host = os.getenv('HOST')
        self.database = os.getenv('DATABASE')
        self.table_name = os.getenv('TABLE_NAME').lower()

    def save_to_db(self, df, user_id):
        try:
            # Tambahkan kolom 'user_id' ke DataFrame
            df['user_id'] = user_id

            # Buat koneksi ke database
            engine = create_engine(f'mysql+pymysql://{self.username}:{self.password}@{self.host}/{self.database}')
            
            # Simpan DataFrame ke database
            df.to_sql(self.table_name, con=engine, if_exists='append', index=False)
            print("Data successfully saved to the database.")
        except SQLAlchemyError as e:
            print(f"An error occurred while saving to the database: {e}")
        finally:
            engine.dispose()


    def get_feature_values(self, **kwargs):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(user=self.username, 
                                                password=self.password, 
                                                host=self.host, 
                                                database=self.database)
            if connection.is_connected():
                print('Successfully connected to the database.')

            cursor = connection.cursor(buffered=True)

            # Mendapatkan user_id dari kwargs
            user_id = kwargs.get('user_id')
            containertype = kwargs.get('containertype')
            masked_name = kwargs.get('masked_name')
            comm_grade_ro = kwargs.get('comm_grade_ro')

            # SQL Query untuk mengambil satu baris data yang sesuai dengan user_id
            query = """
                SELECT MASKED_NAME, CONTAINERTYPE, COMM_GRADE_RO, POD, CUSTOMER_SEGMENTATION, VESSELID
                FROM request_order
                WHERE USER_ID = %s AND CONTAINERTYPE = %s AND MASKED_NAME = %s AND COMM_GRADE_RO = %s
            """
            cursor.execute(query, (user_id, containertype, masked_name.upper(), comm_grade_ro + ';'))

            result = cursor.fetchone()
            print(result)
            if result:
                print("Data found. Returning the result...")
                masked_name, containertype, comm_grade_ro, pod, customer_segmentation, vesselid = result
                dict_result = {
                    'masked_name': masked_name,
                    'containertype': containertype,
                    'comm_grade_ro': comm_grade_ro.replace(';', '').lower(),
                    'pod': pod.lower(),
                    'customer_segmentation': customer_segmentation.lower(),
                    'vesselid': vesselid.lower()
                }
                return dict_result

            else:
                print("Data not found.")
                return None

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    def get_all_feature_values(self, **kwargs):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(user=self.username, 
                                                password=self.password, 
                                                host=self.host, 
                                                database=self.database)
            if connection.is_connected():
                print('Successfully connected to the database.')

            cursor = connection.cursor(buffered=True)

            # Mendapatkan user_id dari kwargs
            user_id = kwargs.get('user_id')

            # SQL Query untuk mengambil semua baris data yang sesuai dengan user_id
            query = """
                SELECT QTY_RO, MASKED_NAME, CONTAINERTYPE, COMM_GRADE_RO, POD, CUSTOMER_SEGMENTATION, VESSELID
                FROM request_order
                WHERE USER_ID = %s
            """
            cursor.execute(query, (user_id,))

            results = cursor.fetchall()
            if results:
                print("Data found. Returning the results...")
                all_results = []
                for result in results:
                    qty_ro, masked_name, containertype, comm_grade_ro, pod, customer_segmentation, vesselid = result
                    dict_result = {
                        'qty_ro': qty_ro,
                        'masked_name': masked_name,
                        'containertype': containertype,
                        'comm_grade_ro': comm_grade_ro.replace(';', '').lower(),
                        'pod': pod.lower(),
                        'customer_segmentation': customer_segmentation.lower(),
                        'vesselid': vesselid.lower()
                    }
                    all_results.append(dict_result)

                return all_results

            else:
                print("No data found for the given user_id.")
                return None

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()
