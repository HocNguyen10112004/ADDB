# Khởi tạo SparkSession
from pyspark.sql import SparkSession
def init_spark():
    spark = SparkSession.builder \
        .appName("FlaskSparkApp") \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
    return spark