package edu.gatech.cse6250.main

import java.text.SimpleDateFormat

import edu.gatech.cse6250.clustering.Metrics
import edu.gatech.cse6250.features.FeatureConstruction
import edu.gatech.cse6250.helper.{ CSVHelper, SparkHelper }
import edu.gatech.cse6250.model.{ Diagnostic, LabResult, Medication }
import edu.gatech.cse6250.phenotyping.T2dmPhenotype
import org.apache.spark.mllib.clustering.{ GaussianMixture, KMeans, StreamingKMeans }
import org.apache.spark.mllib.feature.StandardScaler
import org.apache.spark.mllib.linalg.{ DenseMatrix, Matrices, Vector, Vectors }
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.SparkSession

import scala.io.Source

/**
 * @author Hang Su <hangsu@gatech.edu>,
 * @author Yu Jing <yjing43@gatech.edu>,
 * @author Ming Liu <mliu302@gatech.edu>
 */
object Main {
  def main(args: Array[String]) {
    import org.apache.log4j.{ Level, Logger }

    Logger.getLogger("org").setLevel(Level.WARN)
    Logger.getLogger("akka").setLevel(Level.WARN)

    val spark = SparkHelper.spark
    val sc = spark.sparkContext
    //  val sqlContext = spark.sqlContext

    /** initialize loading of data */
    val (medication, labResult, diagnostic) = loadRddRawData(spark)
    val (candidateMedication, candidateLab, candidateDiagnostic) = loadLocalRawData

    /** conduct phenotyping */
    val phenotypeLabel = T2dmPhenotype.transform(medication, labResult, diagnostic)

    /** feature construction with all features */
    val featureTuples = sc.union(
      FeatureConstruction.constructDiagnosticFeatureTuple(diagnostic),
      FeatureConstruction.constructLabFeatureTuple(labResult),
      FeatureConstruction.constructMedicationFeatureTuple(medication)
    )

    // =========== USED FOR AUTO GRADING CLUSTERING GRADING =============
    // phenotypeLabel.map{ case(a,b) => s"$a\t$b" }.saveAsTextFile("data/phenotypeLabel")
    // featureTuples.map{ case((a,b),c) => s"$a\t$b\t$c" }.saveAsTextFile("data/featureTuples")
    // return
    // ==================================================================

    val rawFeatures = FeatureConstruction.construct(sc, featureTuples)

    val (kMeansPurity, gaussianMixturePurity, streamingPurity) = testClustering(phenotypeLabel, rawFeatures)
    println(f"[All feature] purity of kMeans is: $kMeansPurity%.5f")
    println(f"[All feature] purity of GMM is: $gaussianMixturePurity%.5f")
    println(f"[All feature] purity of StreamingKmeans is: $streamingPurity%.5f")

    /** feature construction with filtered features */
    val filteredFeatureTuples = sc.union(
      FeatureConstruction.constructDiagnosticFeatureTuple(diagnostic, candidateDiagnostic),
      FeatureConstruction.constructLabFeatureTuple(labResult, candidateLab),
      FeatureConstruction.constructMedicationFeatureTuple(medication, candidateMedication)
    )

    val filteredRawFeatures = FeatureConstruction.construct(sc, filteredFeatureTuples)

    val (kMeansPurity2, gaussianMixturePurity2, streamingPurity2) = testClustering(phenotypeLabel, filteredRawFeatures)
    println(f"[Filtered feature] purity of kMeans is: $kMeansPurity2%.5f")
    println(f"[Filtered feature] purity of GMM is: $gaussianMixturePurity2%.5f")
    println(f"[Filtered feature] purity of StreamingKmeans is: $streamingPurity2%.5f")
  }

  // ground truth is columns, predicted classes are rows
  // inspired by https://github.com/apache/spark/blob/master/mllib/src/main/scala/org/apache/spark/mllib/evaluation/MulticlassMetrics.scala
  def confusionMatrix(predAndLabels: RDD[(Int, Int)]): (DenseMatrix) = {
    lazy val labels: Array[Int] = predAndLabels.map(_._2).distinct.collect.toArray.sorted

    // prediction + 1 because our labels start at 1 and predictions start at 0
    val confusion = predAndLabels
      .map {
        case (prediction, label) =>
          ((label, prediction + 1), 1.0)
      }.reduceByKey(_ + _)
      .collectAsMap()

    val n = labels.length
    val values = Array.ofDim[Double]((n) * (n))
    var i = 0
    while (i < n) {
      var j = 0
      while (j < n) {
        values(i + j * n) = confusion.getOrElse((labels(i), labels(j)), 0.0)
        j += 1
      }
      i += 1
    }
    Matrices.dense(n, n, values).asInstanceOf[DenseMatrix].transpose
  }

  def testClustering(phenotypeLabel: RDD[(String, Int)], rawFeatures: RDD[(String, Vector)]): (Double, Double, Double) = {
    import org.apache.spark.mllib.linalg.Matrix
    import org.apache.spark.mllib.linalg.distributed.RowMatrix

    println("phenotypeLabel: " + phenotypeLabel.count)
    /** scale features */
    val scaler = new StandardScaler(withMean = true, withStd = true).fit(rawFeatures.map(_._2))
    val features = rawFeatures.map({ case (patientID, featureVector) => (patientID, scaler.transform(Vectors.dense(featureVector.toArray))) })
    println("features: " + features.count)
    val rawFeatureVectors = features.map(_._2).cache()
    println("rawFeatureVectors: " + rawFeatureVectors.count)

    /** reduce dimension */
    val mat: RowMatrix = new RowMatrix(rawFeatureVectors)
    val pc: Matrix = mat.computePrincipalComponents(10) // Principal components are stored in a local dense matrix.
    val featureVectors = mat.multiply(pc).rows

    val densePc = Matrices.dense(pc.numRows, pc.numCols, pc.toArray).asInstanceOf[DenseMatrix]

    def transform(feature: Vector): Vector = {
      val scaled = scaler.transform(Vectors.dense(feature.toArray))
      Vectors.dense(Matrices.dense(1, scaled.size, scaled.toArray).multiply(densePc).toArray)
    }

    /**
     * TODO: K Means Clustering using spark mllib
     * Train a k means model using the variabe featureVectors as input
     * Set maxIterations =20 and seed as 6250L
     * Assign each feature vector to a cluster(predicted Class)
     * Obtain an RDD[(Int, Int)] of the form (cluster number, RealClass)
     * Find Purity using that RDD as an input to Metrics.purity
     * Remove the placeholder below after your implementation
     */

    val k = 3
    val seed = 6250L
    val maxIter = 20

    val kMeans = new KMeans()
      .setSeed(seed)
      .setK(k)
      .setMaxIterations(maxIter)
      .run(featureVectors)

    val kMeansPredict = kMeans.predict(featureVectors)

    val kMeansPredLabel = features
      .map(_._1)
      .zip(kMeansPredict)
      .join(phenotypeLabel)
      .map(_._2)

    //val kMeansConfusion = kMeansPredLabel
    //  .map {
    //    case (prediction, label) =>
    //      ((label, prediction + 1), 1)
    //  }.reduceByKey(_ + _)
    //  .collectAsMap()

    //println("kMeans Confusion Matrix")
    //val kMeansConfusion = confusionMatrix(kMeansPredLabel)
    //println(kMeansConfusion.toString)

    val kMeansPurity = Metrics.purity(kMeansPredLabel)
    // println("kMeans Purity: " + kMeansPurity)

    /**
     * TODO: GMMM Clustering using spark mllib
     * Train a Gaussian Mixture model using the variabe featureVectors as input
     * Set maxIterations =20 and seed as 6250L
     * Assign each feature vector to a cluster(predicted Class)
     * Obtain an RDD[(Int, Int)] of the form (cluster number, RealClass)
     * Find Purity using that RDD as an input to Metrics.purity
     * Remove the placeholder below after your implementation
     */
    val gMix = new GaussianMixture()
      .setSeed(seed)
      .setK(k)
      .setMaxIterations(maxIter)
      .run(featureVectors)

    val gMixPredict = gMix.predict(featureVectors)

    val gMixPredLabel = features.map(_._1)
      .zip(gMixPredict)
      .join(phenotypeLabel)
      .map(_._2)

    //("GMM Confusion Matrix")
    //val gMixConfusion = confusionMatrix(gMixPredLabel)
    //println(gMixConfusion.toString)

    val gaussianMixturePurity = Metrics.purity(gMixPredLabel)
    // println("GMM Purity: " + gaussianMixturePurity)

    /**
     * TODO: StreamingKMeans Clustering using spark mllib
     * Train a StreamingKMeans model using the variabe featureVectors as input
     * Set the number of cluster K = 3, DecayFactor = 1.0, number of dimensions = 10, weight for each center = 0.5, seed as 6250L
     * In order to feed RDD[Vector] please use latestModel, see more info: https://spark.apache.org/docs/2.2.0/api/scala/index.html#org.apache.spark.mllib.clustering.StreamingKMeans
     * To run your model, set time unit as 'points'
     * Assign each feature vector to a cluster(predicted Class)
     * Obtain an RDD[(Int, Int)] of the form (cluster number, RealClass)
     * Find Purity using that RDD as an input to Metrics.purity
     * Remove the placeholder below after your implementation
     */

    val dim = 10
    val wgt = 0.5
    val decay = 1.0

    val skMeans = new StreamingKMeans()
      .setK(k)
      .setDecayFactor(decay)
      .setRandomCenters(dim, wgt, seed)
      .latestModel()

    val skMeansPredict = skMeans
      .update(featureVectors, decay, "batches")
      .predict(featureVectors)

    val skMeansPredLabel = features.map(_._1)
      .zip(skMeansPredict)
      .join(phenotypeLabel)
      .map(_._2)

    //("Streaming kMeans Confusion Matrix")
    //val skMeansConfusion = confusionMatrix(skMeansPredLabel)
    //println(skMeansConfusion.toString)

    val streamKmeansPurity = Metrics.purity(skMeansPredLabel)
    // println("skMeans Purity: " + streamKmeansPurity)

    (kMeansPurity, gaussianMixturePurity, streamKmeansPurity)
  }

  /**
   * load the sets of string for filtering of medication
   * lab result and diagnostics
   *
   * @return
   */
  def loadLocalRawData: (Set[String], Set[String], Set[String]) = {
    val candidateMedication = Source.fromFile("data/med_filter.txt").getLines().map(_.toLowerCase).toSet[String]
    val candidateLab = Source.fromFile("data/lab_filter.txt").getLines().map(_.toLowerCase).toSet[String]
    val candidateDiagnostic = Source.fromFile("data/icd9_filter.txt").getLines().map(_.toLowerCase).toSet[String]
    (candidateMedication, candidateLab, candidateDiagnostic)
  }

  def sqlDateParser(input: String, pattern: String = "yyyy-MM-dd'T'HH:mm:ssX"): java.sql.Date = {
    val dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssX")
    new java.sql.Date(dateFormat.parse(input).getTime)
  }

  def loadRddRawData(spark: SparkSession): (RDD[Medication], RDD[LabResult], RDD[Diagnostic]) = {
    /* the sql queries in spark required to import sparkSession.implicits._ */
    import spark.implicits._
    val sqlContext = spark.sqlContext

    /* a helper function sqlDateParser may useful here */

    /**
     * load data using Spark SQL into three RDDs and return them
     * Hint:
     * You can utilize edu.gatech.cse6250.helper.CSVHelper
     * through your sparkSession.
     *
     * This guide may helps: https://bit.ly/2xnrVnA
     *
     * Notes:Refer to model/models.scala for the shape of Medication, LabResult, Diagnostic data type.
     * Be careful when you deal with String and numbers in String type.
     * Ignore lab results with missing (empty or NaN) values when these are read in.
     * For dates, use Date_Resulted for labResults and Order_Date for medication.
     *
     */

    /**
     * TODO: implement your own code here and remove
     * existing placeholder code below
     */

    import edu.gatech.cse6250.helper.CSVHelper

    val enc_df = CSVHelper.loadCSVAsTable(
      spark, "data/encounter_INPUT.csv", "enc")
    val dx_df = CSVHelper.loadCSVAsTable(
      spark, "data/encounter_dx_INPUT.csv", "dx")
    val diag_df = sqlContext.sql(
      """
      SELECT enc.Member_ID,
        enc.Encounter_DateTime,
        dx.code
      FROM enc
      INNER JOIN dx
        ON enc.Encounter_ID = dx.Encounter_ID
      """)

    val diagnostic: RDD[Diagnostic] = diag_df.rdd.map(
      r => Diagnostic(
        r(0).toString,
        sqlDateParser(r(1).toString),
        r(2).toString))

    // println("Diag: " + diagnostic.count)

    val med = CSVHelper.loadCSVAsTable(
      spark, "data/medication_orders_INPUT.csv", "med")
    val med_df = sqlContext.sql(
      """
      select med.Member_ID,
        med.Order_Date,
        med.Drug_name
      from med
      """)
    val medication: RDD[Medication] = med_df.rdd.map(
      r => Medication(
        r(0).toString,
        sqlDateParser(r(1).toString),
        r(2).toString))

    // println("Med: " + medication.count)

    val lab = CSVHelper.loadCSVAsTable(
      spark, "data/lab_results_INPUT.csv", "lab")
    val lab_df = sqlContext.sql(
      """
      select lab.Member_ID,
        lab.Date_Resulted,
        lab.Result_Name,
        lab.Numeric_Result
      from lab
      """)

    val labFiltered = lab_df.filter(
      lab_df("Numeric_Result").isNotNull
        && lab_df("Numeric_Result") != "")

    val labResult: RDD[LabResult] =
      labFiltered.rdd.map(
        r => LabResult(
          r(0).toString,
          sqlDateParser(r(1).toString),
          r(2).toString,
          r(3).toString.replace(",", "").toDouble))

    // println("Lab Results: " + labResult.count)

    (medication, labResult, diagnostic)
  }

}
