// Databricks notebook source
// Q2 [25 pts]: Analyzing a Large Graph with Spark/Scala on Databricks

// STARTER CODE - DO NOT EDIT THIS CELL
import org.apache.spark.sql.functions.desc
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._
import spark.implicits._

// COMMAND ----------

// STARTER CODE - DO NOT EDIT THIS CELL
// Definfing the data schema
val customSchema = StructType(Array(StructField("answerer", IntegerType, true), StructField("questioner", IntegerType, true),
    StructField("timestamp", LongType, true)))

// COMMAND ----------

// STARTER CODE - YOU CAN LOAD ANY FILE WITH A SIMILAR SYNTAX.
// MAKE SURE THAT YOU REPLACE THE examplegraph.csv WITH THE mathoverflow.csv FILE BEFORE SUBMISSION.
val df = spark.read
   .format("com.databricks.spark.csv")
   .option("header", "false") // Use first line of all files as header
   .option("nullValue", "null")
   .schema(customSchema)
   .load("/FileStore/tables/mathoverflow.csv")

// COMMAND ----------

//display(df)
df.show()

// COMMAND ----------

// PART 1: Remove the pairs where the questioner and the answerer are the same person.
// ALL THE SUBSEQUENT OPERATIONS MUST BE PERFORMED ON THIS FILTERED DATA

// ENTER THE CODE BELOW
val filterDF = df
  .filter($"answerer" !== $"questioner")
display(filterDF)

// COMMAND ----------

// PART 2: The top-3 individuals who answered the most number of questions - sorted in descending order - if tie, the one with lower node-id gets listed first : the nodes with the highest out-degrees.

// ENTER THE CODE BELOW
val top3Answerers = filterDF.groupBy($"answerer").count().sort(col("count").desc, $"answerer").limit(3).withColumnRenamed("count", "questions_answered")
display(top3Answerers)

// COMMAND ----------

// PART 3: The top-3 individuals who asked the most number of questions - sorted in descending order - if tie, the one with lower node-id gets listed first : the nodes with the highest in-degree.

// ENTER THE CODE BELOW
val top3Questioners = filterDF.groupBy($"questioner").count().sort(col("count").desc, $"questioner").limit(3).withColumnRenamed("count", "questions_asked")
display(top3Questioners)

// COMMAND ----------

// PART 4: The top-5 most common asker-answerer pairs - sorted in descending order - if tie, the one with lower value node-id in the first column (u->v edge, u value) gets listed first.

// ENTER THE CODE BELOW
val top5QuestionerAnswererPars = filterDF.groupBy($"questioner", $"answerer").count().sort(col("count").desc, $"answerer", $"questioner").limit(5)
display(top5QuestionerAnswererPars)

// COMMAND ----------

// PART 5: Number of interactions (questions asked/answered) over the months of September-2010 to December-2010 (i.e. from September 1, 2010 to December 31, 2010). List the entries by month from September to December.

// Reference: https://www.obstkel.com/blog/spark-sql-date-functions
// Read in the data and extract the month and year from the date column.
// Hint: Check how we extracted the date from the timestamp.

// ENTER THE CODE BELOW
val monthsDF = filterDF.withColumn("date", from_unixtime($"timestamp")).drop("timestamp").filter($"date".geq(lit("2010-09-01")) && $"date".leq(lit("2012-12-31"))).withColumn("month", date_format(to_date($"date", "yyyy-MM-dd"), "M")).groupBy($"month").count().withColumnRenamed("count", "total_interactions")
display(monthsDF)

// COMMAND ----------

// PART 6: List the top-3 individuals with the maximum overall activity, i.e. total questions asked and questions answered.

// ENTER THE CODE BELOW
val a = filterDF.groupBy($"answerer").count().sort(col("count").desc, $"answerer").withColumnRenamed("answerer", "userID").withColumnRenamed("count", "a_activity")
val q = filterDF.groupBy($"questioner").count().sort(col("count").desc, $"questioner").withColumnRenamed("questioner", "userID").withColumnRenamed("count", "q_activity")
val totalDF = a.join(q,Seq("userID")).withColumn("total_activity", $"a_activity" + $"q_activity").drop("a_activity").drop("q_activity").sort($"total_activity".desc, $"userID").limit(3)
display(totalDF)
