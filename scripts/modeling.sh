#!/bin/bash
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/anaconda3/bin/python
export PYSPARK_PYTHON=/home/ubuntu/anaconda3/bin/python
export PYSPARK_DRIVER_PYTHON_OPTS=

/home/ubuntu/anaconda3/bin/spark-submit \
--master local[4] \
--executor-memory 1G \
--driver-memory 1G \
--conf spark.sql.warehouse.dir="file:///tmp/spark-warehouse" \
--packages com.databricks:spark-csv_2.11:1.5.0 \
--packages com.amazonaws:aws-java-sdk-pom:1.10.34 \
--packages org.apache.hadoop:hadoop-aws:2.7.3 \
/home/ubuntu/cardstorm/src/modeling.py 1>/home/ubuntu/cardstorm_logs/model_stdout.log 2>/home/ubuntu/cardstorm_logs/model_stderr.log
