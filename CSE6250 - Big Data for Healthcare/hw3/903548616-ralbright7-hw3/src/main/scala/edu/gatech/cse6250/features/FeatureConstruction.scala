package edu.gatech.cse6250.features

import edu.gatech.cse6250.model.{ Diagnostic, LabResult, Medication }
import org.apache.spark.SparkContext
import org.apache.spark.mllib.linalg.{ Vector, Vectors }
import org.apache.spark.rdd.RDD

/**
 * @author Hang Su
 */
object FeatureConstruction {

  /**
   * ((patient-id, feature-name), feature-value)
   */
  type FeatureTuple = ((String, String), Double)

  /**
   * Aggregate feature tuples from diagnostic with COUNT aggregation,
   *
   * @param diagnostic RDD of diagnostic
   * @return RDD of feature tuples
   */
  def constructDiagnosticFeatureTuple(diagnostic: RDD[Diagnostic]): RDD[FeatureTuple] = {
    /**
     * TODO implement your own code here and remove existing
     * placeholder code
     */
    diagnostic.map(
      r => ((r.patientID, r.code), 1.0)).reduceByKey(_ + _)
  }

  /**
   * Aggregate feature tuples from medication with COUNT aggregation,
   *
   * @param medication RDD of medication
   * @return RDD of feature tuples
   */
  def constructMedicationFeatureTuple(medication: RDD[Medication]): RDD[FeatureTuple] = {
    /**
     * TODO implement your own code here and remove existing
     * placeholder code
     */
    medication.map(
      r => ((r.patientID, r.medicine), 1.0)).reduceByKey(_ + _)
  }

  /**
   * Aggregate feature tuples from lab result, using AVERAGE aggregation
   *
   * @param labResult RDD of lab result
   * @return RDD of feature tuples
   */
  def constructLabFeatureTuple(labResult: RDD[LabResult]): RDD[FeatureTuple] = {
    /**
     * TODO implement your own code here and remove existing
     * placeholder code
     */
    val labResultSum = labResult.map(
      r => ((r.patientID, r.testName), r.value)).reduceByKey(_ + _)

    val labResultCt = labResult.map(
      r => ((r.patientID, r.testName), 1.0)).reduceByKey(_ + _)

    val labResultJoin = labResultSum join labResultCt

    labResultJoin.map(
      r => (r._1, r._2._1 / r._2._2))
  }

  /**
   * Aggregate feature tuple from diagnostics with COUNT aggregation, but use code that is
   * available in the given set only and drop all others.
   *
   * @param diagnostic   RDD of diagnostics
   * @param candiateCode set of candidate code, filter diagnostics based on this set
   * @return RDD of feature tuples
   */
  def constructDiagnosticFeatureTuple(diagnostic: RDD[Diagnostic], candiateCode: Set[String]): RDD[FeatureTuple] = {
    /**
     * TODO implement your own code here and remove existing
     * placeholder code
     */

    diagnostic.filter(
      r => candiateCode.contains(r.code)).map(
        r => ((r.patientID, r.code), 1.0)).reduceByKey(_ + _)
  }

  /**
   * Aggregate feature tuples from medication with COUNT aggregation, use medications from
   * given set only and drop all others.
   *
   * @param medication          RDD of diagnostics
   * @param candidateMedication set of candidate medication
   * @return RDD of feature tuples
   */
  def constructMedicationFeatureTuple(medication: RDD[Medication], candidateMedication: Set[String]): RDD[FeatureTuple] = {
    /**
     * TODO implement your own code here and remove existing
     * placeholder code
     */
    medication.filter(
      r => candidateMedication.contains(r.medicine)).map(
        r => ((r.patientID, r.medicine), 1.0)).reduceByKey(_ + _)
  }

  /**
   * Aggregate feature tuples from lab result with AVERAGE aggregation, use lab from
   * given set of lab test names only and drop all others.
   *
   * @param labResult    RDD of lab result
   * @param candidateLab set of candidate lab test name
   * @return RDD of feature tuples
   */
  def constructLabFeatureTuple(labResult: RDD[LabResult], candidateLab: Set[String]): RDD[FeatureTuple] = {
    /**
     * TODO implement your own code here and remove existing
     * placeholder code
     */
    val labResultSum = labResult.filter(
      r => candidateLab.contains(r.testName)).map(
        r => ((r.patientID, r.testName), r.value)).reduceByKey(_ + _)

    val labResultCt = labResult.filter(
      r => candidateLab.contains(r.testName)).map(
        r => ((r.patientID, r.testName), 1.0)).reduceByKey(_ + _)

    val labResultJoin = labResultSum join labResultCt

    labResultJoin.map(
      r => (r._1, r._2._1 / r._2._2))
  }

  /**
   * Given a feature tuples RDD, construct features in vector
   * format for each patient. feature name should be mapped
   * to some index and convert to sparse feature format.
   *
   * @param sc      SparkContext to run
   * @param feature RDD of input feature tuples
   * @return
   */
  def construct(sc: SparkContext, feature: RDD[FeatureTuple]): RDD[(String, Vector)] = {

    /** save for later usage */
    feature.cache()

    /** create a feature name to id map */
    val features_idx = feature.map(_._1._2).distinct.collect.zipWithIndex.toMap

    // this gets it into the patientFeatures map
    val globalFeatures = sc.broadcast(features_idx)

    /** transform input feature */

    /**
     * Functions maybe helpful:
     * collect
     * groupByKey
     */
    val patientFeatures = feature.map(
      r => (r._1._1, (r._1._2, r._2))).groupByKey()

    /**
     * TODO implement your own code here and remove existing
     * placeholder code
     */

    val result = patientFeatures.map {
      case (patient, features) =>
        val numFeatures = globalFeatures.value.size
        val patientFeatures = features.toList.map {
          case (featureName, featureValue) =>
            (globalFeatures.value(featureName), featureValue)
        }
        val patientVector = Vectors.sparse(numFeatures, patientFeatures)
        val record = (patient, patientVector)
        record
    }
    result

    /** The feature vectors returned can be sparse or dense. It is advisable to use sparse */

  }
}

