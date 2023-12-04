/**
 *
 * students: please put your implementation in this file!
 */
package edu.gatech.cse6250.jaccard

import edu.gatech.cse6250.model._
import edu.gatech.cse6250.model.{ EdgeProperty, VertexProperty }
import org.apache.spark.graphx._
import org.apache.spark.rdd.RDD

object Jaccard {

  def jaccardSimilarityOneVsAll(graph: Graph[VertexProperty, EdgeProperty], patientID: Long): List[Long] = {
    /**
     * Given a patient ID, compute the Jaccard similarity w.r.t. to all other patients.
     * Return a List of top 10 patient IDs ordered by the highest to the lowest similarity.
     * For ties, random order is okay. The given patientID should be excluded from the result.
     */

    /** Remove this placeholder and implement your code */

    val neighbors = graph.subgraph(
      vpred = {
        case (id, attr) =>
          attr.isInstanceOf[PatientProperty]
      }).collectNeighborIds(EdgeDirection.Out).map(
        r => r._1).collect().toSet

    val allNeighbors = graph.collectNeighborIds(EdgeDirection.Out)

    val otherNeighbors = allNeighbors.filter(
      r => neighbors.contains(r._1) && r._1.toLong != patientID)

    val patientNeighbors = allNeighbors.filter(
      r => r._1.toLong == patientID).map(
        r => r._2).flatMap(
          r => r).collect.toSet

    val scores = otherNeighbors.map(
      r => (r._1, jaccard(patientNeighbors, r._2.toSet)))

    scores.takeOrdered(10)(
      Ordering[Double].reverse.on(
        r => r._2)).map(
        _._1.toLong).toList
  }

  def jaccardSimilarityAllPatients(graph: Graph[VertexProperty, EdgeProperty]): RDD[(Long, Long, Double)] = {
    /**
     * Given a patient, med, diag, lab graph, calculate pairwise similarity between all
     * patients. Return a RDD of (patient-1-id, patient-2-id, similarity) where
     * patient-1-id < patient-2-id to avoid duplications
     */

    /** Remove this placeholder and implement your code */
    val sc = graph.edges.sparkContext

    val neighbors = graph.subgraph(
      vpred = {
        case (id, attr) =>
          attr.isInstanceOf[PatientProperty]
      }).collectNeighborIds(EdgeDirection.Out).map(
        r => r._1).collect.toSet

    val allNeighbors = graph.collectNeighborIds(EdgeDirection.Out)

    val patientNeighbors = allNeighbors.filter(
      r => neighbors.contains(r._1))

    val cartesian = patientNeighbors.cartesian(patientNeighbors).filter(
      r => r._1._1 < r._2._1)

    cartesian.map(
      r => (
        r._1._1,
        r._2._1,
        jaccard(
          r._1._2.toSet,
          r._2._2.toSet)))
  }

  def jaccard[A](a: Set[A], b: Set[A]): Double = {
    /**
     * Helper function
     *
     * Given two sets, compute its Jaccard similarity and return its result.
     * If the union part is zero, then return 0.
     */

    /** Remove this placeholder and implement your code */
    if (a.isEmpty || b.isEmpty) {
      0.0
    } else {
      a.intersect(b).size.toDouble / a.union(b).size.toDouble
    }
  }
}
