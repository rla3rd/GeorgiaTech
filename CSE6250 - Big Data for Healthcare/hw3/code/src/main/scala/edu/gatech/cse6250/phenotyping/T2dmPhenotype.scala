package edu.gatech.cse6250.phenotyping

import edu.gatech.cse6250.model.{ Diagnostic, LabResult, Medication }
import org.apache.spark.rdd.RDD

/**
 * @author Hang Su <hangsu@gatech.edu>,
 * @author Sungtae An <stan84@gatech.edu>,
 */
object T2dmPhenotype {

  /** Hard code the criteria */
  val T1DM_DX = Set("250.01", "250.03", "250.11", "250.13", "250.21", "250.23", "250.31", "250.33", "250.41", "250.43",
    "250.51", "250.53", "250.61", "250.63", "250.71", "250.73", "250.81", "250.83", "250.91", "250.93")

  val T2DM_DX = Set("250.3", "250.32", "250.2", "250.22", "250.9", "250.92", "250.8", "250.82", "250.7", "250.72", "250.6",
    "250.62", "250.5", "250.52", "250.4", "250.42", "250.00", "250.02")

  val T1DM_MED = Set("lantus", "insulin glargine", "insulin aspart", "insulin detemir", "insulin lente", "insulin nph", "insulin reg", "insulin,ultralente")

  val T2DM_MED = Set("chlorpropamide", "diabinese", "diabanase", "diabinase", "glipizide", "glucotrol", "glucotrol xl",
    "glucatrol ", "glyburide", "micronase", "glynase", "diabetamide", "diabeta", "glimepiride", "amaryl",
    "repaglinide", "prandin", "nateglinide", "metformin", "rosiglitazone", "pioglitazone", "acarbose",
    "miglitol", "sitagliptin", "exenatide", "tolazamide", "acetohexamide", "troglitazone", "tolbutamide",
    "avandia", "actos", "actos", "glipizide")

  /**
   * Transform given data set to a RDD of patients and corresponding phenotype
   *
   * @param medication medication RDD
   * @param labResult  lab result RDD
   * @param diagnostic diagnostic code RDD
   * @return tuple in the format of (patient-ID, label). label = 1 if the patient is case, label = 2 if control, 3 otherwise
   */
  def transform(medication: RDD[Medication], labResult: RDD[LabResult], diagnostic: RDD[Diagnostic]): RDD[(String, Int)] = {
    /**
     * Remove the place holder and implement your code here.
     * Hard code the medication, lab, icd code etc. for phenotypes like example code below.
     * When testing your code, we expect your function to have no side effect,
     * i.e. do NOT read from file or write file
     *
     * You don't need to follow the example placeholder code below exactly, but do have the same return type.
     *
     * Hint: Consider case sensitivity when doing string comparisons.
     */

    val sc = medication.sparkContext

    /** Hard code the criteria */
    // val type1_dm_dx = Set("code1", "250.03")
    // val type1_dm_med = Set("med1", "insulin nph")
    // use the given criteria above like T1DM_DX, T2DM_DX, T1DM_MED, T2DM_MED and hard code DM_RELATED_DX criteria as well

    val DM_RELATED_DX = Set("790.21", "790.22", "790.2", "790.29", "648.81", "648.82", "648.83", "648.84", "648", "648",
      "648.01", "648.02", "648.03", "648.04", "791.5", "277.7", "V77.1", "256.4")

    val total = diagnostic.map(_.patientID).distinct
    // println("Total: " + total.count)

    val type1_dx = diagnostic.filter(
      r => T1DM_DX.contains(r.code)).map(
        _.patientID).distinct

    // println("Type 1: " + type1_dx.count)

    val no_type1_dx = total subtract type1_dx

    // println("No Type 1: " + no_type1_dx.count)

    val type2_dx = diagnostic.filter(
      r => !T1DM_DX.contains(r.code)).filter(
        r => T2DM_DX.contains(r.code)
      ).map(_.patientID).distinct

    // println("Type 2: " + type2_dx.count)

    val t1_med = medication.filter(
      r => T1DM_MED.contains(r.medicine.toLowerCase)).map(
        _.patientID).distinct

    val no_t1_med = type2_dx subtract t1_med

    val case1 = type2_dx intersection no_t1_med

    // println("Case 1: " + case1.count)

    val no_t2_med = medication.filter(
      r => !T2DM_MED.contains(r.medicine.toLowerCase)).map(
        _.patientID).distinct

    val notcase1 = type2_dx intersection t1_med intersection no_t2_med

    // println("Not Case 1: " + notcase1.count)

    val t2_med = medication.filter(
      r => T2DM_MED.contains(r.medicine.toLowerCase)).map(
        _.patientID).distinct

    val case2 = notcase1 subtract t2_med

    // println("Case 2: " + case2.count)

    val notcase2 = notcase1 subtract case2

    // println("Not Case 2: " + notcase2.count)

    val notcase2set = notcase2.collect.toSet

    val both_meds = medication.filter(
      r => notcase2set.contains(r.patientID))

    val both_meds_t1date = both_meds.filter(
      r => T1DM_MED.contains(
        r.medicine.toLowerCase)).map(
        r => (r.patientID, r.date.getTime())).reduceByKey(
          Math.min)

    val both_meds_t2date = both_meds.filter(
      r => T2DM_MED.contains(
        r.medicine.toLowerCase)).map(
        r => (r.patientID, r.date.getTime())).reduceByKey(
          Math.min)

    val case3 = both_meds_t1date.join(
      both_meds_t2date).filter(
      r => r._2._1 > r._2._2).map(_._1)

    // println("Case 3: " + case3.count)

    val case123 = sc.union(case1, case2, case3)

    /** Find CASE Patients */
    val casePatients = case123.map((_, 1))

    val totalLab = labResult.map(r => r.patientID).distinct

    val hasGlucose = labResult.filter(
      r => r.testName.toLowerCase.contains("glucose")).map(
        r => r.patientID).distinct

    // println("Has Glucose: " + hasGlucose.count)

    /*
      # ABNORMAL LAB VALUES: CONTROLS
      'HbA1c' >=6.0%
      OR
      'Hemoglobin A1c' >= 6.0%
      OR
      'Fasting Glucose' >= 110 mg/dL
      OR
      'Fasting blood glucose' >= 110 mg/dL
      OR
      'fasting plasma glucose' >= 110 mg/dL
      OR
      'Glucose' > 110 mg/dL
      OR
      'glucose' > 110 mg/dL
      OR
      'Glucose, Serum' > 110 mg/dL
    */

    val hbAic = labResult.filter(
      r => r.testName.toLowerCase.contains("hba1c")
        && r.value >= 6.0).map(
        r => r.patientID)

    val hA1c = labResult.filter(
      r => r.testName.toLowerCase.contains("hemoglobin")
        && r.testName.toLowerCase.contains("a1c")
        && r.value >= 6.0).map(
        r => r.patientID)

    val fg = labResult.filter(
      r => r.testName.toLowerCase.contains("fasting")
        && r.testName.toLowerCase.contains("glucose")
        && r.value >= 110.0).map(
        r => r.patientID)

    val fbg = labResult.filter(
      r => r.testName.toLowerCase.contains("fasting")
        && r.testName.toLowerCase.contains("blood")
        && r.testName.toLowerCase.contains("glucose")
        && r.value >= 110.0).map(
        r => r.patientID)

    val fpg = labResult.filter(
      r => r.testName.toLowerCase.contains("fasting")
        && r.testName.toLowerCase.contains("plasma")
        && r.testName.toLowerCase.contains("glucose")
        && r.value >= 110.0).map(
        r => r.patientID)

    val gl = labResult.filter(
      r => r.testName.toLowerCase.contains("glucose")
        && r.value > 110.0).map(
        r => r.patientID)

    val gL = labResult.filter(
      r => r.testName.toLowerCase.contains("glucose")
        && r.value > 110.0).map(
        r => r.patientID)

    val gs = labResult.filter(
      r => r.testName.toLowerCase.contains("glucose")
        && r.testName.toLowerCase.contains("serum")
        && r.value > 110.0).map(
        r => r.patientID)

    val abnormal = sc.union(hbAic, hA1c, fg, fbg, fpg, gl, gL, gs).distinct

    // println("Abnormal Lab: " + abnormal.count)

    val filtAbnormal = hasGlucose subtract abnormal

    // println("Glucose Not Abnormal Lab: " + filtAbnormal.count)

    val dm_dx = diagnostic.filter(
      r => DM_RELATED_DX.contains(r.code)).map(
        r => r.patientID).distinct

    val code250 = diagnostic.filter(
      r => r.code.startsWith("250.")).map(
        r => r.patientID)

    val dmrd = dm_dx union code250 distinct

    val controlP = filtAbnormal subtract dmrd

    // println("Control: " + controlP.count)

    /** Find CONTROL Patients */
    val controlPatients = controlP.map((_, 2))

    val otherPatients = total subtract case123 subtract controlP
    // println("Others: " + otherPatients.count)

    /** Find OTHER Patients */
    val others = otherPatients.map((_, 3))

    /** Once you find patients for each group, make them as a single RDD[(String, Int)] */
    val phenotypeLabel = sc.union(casePatients, controlPatients, others)

    val calcs = stat_calc(labResult, phenotypeLabel)
    // println(calcs)

    /** Return */
    phenotypeLabel
  }

  /**
   * calculate specific stats given phenotype labels and corresponding data set rdd
   * @param labResult  lab result RDD
   * @param phenotypeLabel phenotype label return from T2dmPhenotype.transfrom
   * @return tuple in the format of (case_mean, control_mean, other_mean).
   *         case_mean = mean Glucose lab test results of case group
   *         control_mean = mean Glucose lab test results of control group
   *         other_mean = mean Glucose lab test results of unknown group
   *         Attention: order of the three stats in the returned tuple matters!
   */
  def stat_calc(labResult: RDD[LabResult], phenotypeLabel: RDD[(String, Int)]): (Double, Double, Double) = {
    /**
     * you need to hardcode the feature name and the type of stat:
     * e.g. calculate "mean" of "Glucose" lab test result of each group: case, control, unknown
     *
     * The feature name should be "Glucose" exactly with considering case sensitivity.
     * i.e. "Glucose" and "glucose" are counted, but features like "fasting glucose" should not be counted.
     *
     * Hint: rdd dataset can directly call statistic method. Details can be found on course website.
     *
     */

    val caseP = phenotypeLabel.filter(
      r => r._2 == 1).map(
        r => r._1)

    val caseSet = caseP.collect.toSet

    val controlP = phenotypeLabel.filter(
      r => r._2 == 2).map(
        r => r._1)

    val controlSet = controlP.collect.toSet

    val otherP = phenotypeLabel.filter(
      r => r._2 == 3).map(
        r => r._1)

    val otherSet = otherP.collect.toSet

    val glucoseLabs = labResult.filter(
      r => r.testName.toLowerCase.equals("glucose")).map(
        r => (r.patientID, r.value))

    val case_mean = glucoseLabs.filter(
      r => caseSet.contains(r._1)).map(
        r => r._2).mean

    val control_mean = glucoseLabs.filter(
      r => controlSet.contains(r._1)).map(
        r => r._2).mean

    val other_mean = glucoseLabs.filter(
      r => otherSet.contains(r._1)).map(
        r => r._2).mean

    (case_mean, control_mean, other_mean)
  }
}