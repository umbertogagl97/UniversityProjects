# Databricks notebook source
#esempio caricamento da mongoDB
from pyspark.sql import SparkSession
database = "final_project"
collection_movies = "movies" #your collection name
connectionString= "mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false"
spark = SparkSession\
.builder\
.config('spark.mongodb.input.uri',connectionString)\
.config('spark.mongodb.output.uri', connectionString)\
.config('spark.jars.packages', 'org.mongodb.spark:mongo-spark-connector_2.12:3.0.1')\
.getOrCreate()
# Reading from MongoDB
df_movies = spark.read\
.format("mongo")\
.option("uri", connectionString)\
.option("database", database)\
.option("collection", collection_movies)\
.load()
df.printSchema()

# COMMAND ----------

#caricamento dataframe
file_location = "/FileStore/tables/"
file_type = "csv"
# CSV options
infer_schema = "false"
first_row_is_header = "false"
delimiter = ","

df_rating = spark.read.format(file_type) \
  .option("inferSchema", "true") \
  .option("header", "true") \
  .option("sep", delimiter) \
  .load(file_location+"ratings.cs")
df_rating=df_rating.select("userID","movieID","rating")
df_rating.printSchema()
# File location and type
file_location = "/FileStore/tables/movies.csv"
file_type = "csv"


df_movies = spark.read.format(file_type) \
  .option("inferSchema", "true") \
  .option("header", "true") \
  .option("sep", delimiter) \
  .load(file_location)
df_movies.printSchema()




# COMMAND ----------

#split in train e test set
(train, test) = df_rating.randomSplit([0.8, 0.2], seed = 2020)

# COMMAND ----------

#creazione modello ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator

als = ALS(
         userCol="userID", 
         itemCol="movieID",
         ratingCol="rating", 
         nonnegative = True, 
         implicitPrefs = False,
         coldStartStrategy="drop"
)

# COMMAND ----------

#evaluator model e set iperparametri griglia
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.evaluation import RegressionEvaluator

#creazione di una griglia di iperparametri con i valori da testare
param_grid = ParamGridBuilder() \
            .addGrid(als.rank, [100,150]) \
            .addGrid(als.regParam, [.1, .15]) \
            .build()

# Define evaluator as RMSE and print length of evaluator
evaluator = RegressionEvaluator(
           metricName="rmse", 
           labelCol="rating", 
           predictionCol="prediction") 
print ("Num models to be tested: ", len(param_grid))

# COMMAND ----------

#cross-validation model
cv = CrossValidator(estimator=als, estimatorParamMaps=param_grid, evaluator=evaluator, numFolds=2)

# COMMAND ----------

#crossvalidation e testing
import pandas as pd
import matplotlib.pyplot as plt
from numpy import savetxt
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_diabetes
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

#esecuzione crossvalidation
model = cv.fit(train)
#estrazione best model dalla validazione
best_model = model.bestModel
#testing
test_predictions = best_model.transform(test)
RMSE = evaluator.evaluate(test_predictions)
print(RMSE)

# COMMAND ----------

#print results
print("**Best Model**")
# Print "Rank"
print("  Rank:", best_model._java_obj.parent().getRank())
# Print "MaxIter"
print("  MaxIter:", best_model._java_obj.parent().getMaxIter())
# Print "RegParam"
print("  RegParam:", best_model._java_obj.parent().getRegParam())

# COMMAND ----------

#Generazioni 10 raccomandazioni per tutti gli utenti
recommendations = best_model.recommendForAllUsers(10)
recommendations.show()

# COMMAND ----------

#modifica dataframe per dividere movieID e rating
from pyspark.sql.functions import explode,col

nrecommendations = recommendations\
    .withColumn("rec_exp", explode("recommendations"))\
    .select('userID', col("rec_exp.movieID"), col("rec_exp.rating"))
nrecommendations.limit(10).show()

# COMMAND ----------

#inserimento title nel dataframe e salvataggio tabella
df_recc_tot=nrecommendations.join(df_movies, on='movieId').sort("rating", ascending = False)
df_recc_tot.write.saveAsTable("film_raccomandati")

# COMMAND ----------

#join dei due dataframe
movie_ratings = df_rating.join(df_movies, ['movieId'], 'left')
movie_ratings.show()
