/**
 * @author Hang Su <hangsu@gatech.edu>.
 */

package edu.gatech.cse6250.graphconstruct

import edu.gatech.cse6250.model._
import org.apache.spark.graphx._
import org.apache.spark.rdd.RDD

object GraphLoader {
  /**
   * Generate Bipartite Graph using RDDs
   *
   * @input: RDDs for Patient, LabResult, Medication, and Diagnostic
   * @return: Constructed Graph
   *
   */
  var vertexPatient: RDD[(VertexId, VertexProperty)] = _
  var vertexLabResult: RDD[(VertexId, VertexProperty)] = _
  var vertexMedication: RDD[(VertexId, VertexProperty)] = _
  var vertexDiagnostic: RDD[(VertexId, VertexProperty)] = _

  var edgeLabResult: RDD[Edge[EdgeProperty]] = _
  var edgeMedication: RDD[Edge[EdgeProperty]] = _
  var edgeDiagnostic: RDD[Edge[EdgeProperty]] = _

  def load(patients: RDD[PatientProperty], labResults: RDD[LabResult],
    medications: RDD[Medication], diagnostics: RDD[Diagnostic]): Graph[VertexProperty, EdgeProperty] = {

    val sc = patients.sparkContext

    vertexPatient = patients.map(
      patient => (
        patient.patientID.toLong,
        patient.asInstanceOf[VertexProperty]))

    val last_lab = labResults.map(
      r => (
        (r.patientID, r.labName), r)).reduceByKey(
        (r1, r2) =>
          if (r1.date > r2.date) r1 else r2).map {
          case (k, v) => v
        }

    val last_med = medications.map(
      r => (
        (r.patientID, r.medicine), r)).reduceByKey(
        (r1, r2) =>
          if (r1.date > r2.date) r1 else r2).map {
          case (k, v) => v
        }

    val last_diag = diagnostics.map(
      r => (
        (r.patientID, r.icd9code), r)).reduceByKey(
        (r1, r2) =>
          if (r1.date > r2.date) r1 else r2).map {
          case (k, v) => v
        }

    val p_ct = vertexPatient.count()

    var offset: Long = p_ct + 1

    val vertexLabResultIdx = last_lab.map(
      _.labName).distinct.zipWithIndex.map {
        case (v, ind) =>
          ((ind + offset), v)
      }

    vertexLabResult = vertexLabResultIdx.map {
      case (k, v) => (k, LabResultProperty(v))
    }

    offset += vertexLabResult.count()

    val vertexMedicationIdx = last_med.map(
      _.medicine).distinct.zipWithIndex.map {
        case (v, ind) =>
          ((ind + offset), v)
      }

    vertexMedication = vertexMedicationIdx.map {
      case (k, v) => (k, MedicationProperty(v))
    }

    offset += vertexMedication.count()

    val vertexDiagnosticIdx = last_diag.map(
      _.icd9code).distinct.zipWithIndex.map {
        case (v, ind) =>
          ((ind + offset), v)
      }

    vertexDiagnostic = vertexDiagnosticIdx.map {
      case (k, v) => (k, DiagnosticProperty(v))
    }

    val labMap = sc.broadcast(vertexLabResultIdx.map(
      r => (r._2, r._1)).collect.toMap)

    val medMap = sc.broadcast(vertexMedicationIdx.map(
      r => (r._2, r._1)).collect.toMap)

    val diagMap = sc.broadcast(vertexDiagnosticIdx.map(
      r => (r._2, r._1)).collect.toMap)

    val edgePatLab = last_lab.map(
      r =>
        Edge(
          r.patientID.toLong,
          labMap.value(r.labName),
          PatientLabEdgeProperty(r).asInstanceOf[EdgeProperty]))

    val edgeLabPat = last_lab.map(
      r =>
        Edge(
          labMap.value(r.labName),
          r.patientID.toLong,
          PatientLabEdgeProperty(r).asInstanceOf[EdgeProperty]))

    val edgePatMed = last_med.map(
      r =>
        Edge(
          r.patientID.toLong,
          medMap.value(r.medicine),
          PatientMedicationEdgeProperty(r).asInstanceOf[EdgeProperty]))

    val edgeMedPat = last_med.map(
      r =>
        Edge(
          r.patientID.toLong,
          medMap.value(r.medicine),
          PatientMedicationEdgeProperty(r).asInstanceOf[EdgeProperty]))

    val edgePatDiag = last_diag.map(
      r =>
        Edge(
          r.patientID.toLong,
          diagMap.value(r.icd9code),
          PatientDiagnosticEdgeProperty(r).asInstanceOf[EdgeProperty]))

    val edgeDiagPat = last_diag.map(
      r =>
        Edge(
          r.patientID.toLong,
          diagMap.value(r.icd9code),
          PatientDiagnosticEdgeProperty(r).asInstanceOf[EdgeProperty]))

    val edgePatientLabResults = sc.union(edgePatLab, edgeLabPat)
    val edgePatientMedication = sc.union(edgePatMed, edgeMedPat)
    val edgePatientDiagnostic = sc.union(edgePatDiag, edgeDiagPat)

    val vertices = sc.union(
      vertexPatient,
      vertexLabResult,
      vertexMedication,
      vertexDiagnostic)

    val edges = sc.union(
      edgePatientLabResults,
      edgePatientMedication,
      edgePatientDiagnostic)

    // Making Graph
    val graph: Graph[VertexProperty, EdgeProperty] = Graph[VertexProperty, EdgeProperty](vertices, edges)

    graph
  }
}
