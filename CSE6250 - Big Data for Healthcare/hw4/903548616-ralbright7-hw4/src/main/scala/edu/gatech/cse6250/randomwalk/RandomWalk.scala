package edu.gatech.cse6250.randomwalk

import edu.gatech.cse6250.model.{ PatientProperty, EdgeProperty, VertexProperty }
import org.apache.spark.graphx._

object RandomWalk {

  def randomWalkOneVsAll(graph: Graph[VertexProperty, EdgeProperty], patientID: Long, numIter: Int = 100, alpha: Double = 0.15): List[Long] = {
    /**
     * Given a patient ID, compute the random walk probability w.r.t. to all other patients.
     * Return a List of patient IDs ordered by the highest to the lowest similarity.
     * For ties, random order is okay
     */

    // hevaily borrowed from
    // GraphX's PageRank.scala source file runWithOptions and runUpdate function
    // and combined into one function
    // https://github.com/apache/spark/blob/master/graphx/src/main/scala/org/apache/spark/graphx/lib/PageRank.scala
    val srcNode: VertexId = patientID
    def delta(u: VertexId, v: VertexId): Double = {
      if (u == v) 1.0 else 0.0
    }

    var rank: Graph[Double, Double] = graph
      .outerJoinVertices(graph.outDegrees) {
        (vid, vdata, deg) => deg.getOrElse(0)
      }
      .mapTriplets(e => 1.0 / e.srcAttr, TripletFields.Src)
      .mapVertices {
        (k, v) =>
          if (!(k != srcNode)) 1.0 else 0.0
      }

    var i = 0
    var prevRank: Graph[Double, Double] = null

    while (i < numIter) {
      rank.cache()

      val rankUpdates = rank.aggregateMessages[Double](
        ctx =>
          ctx.sendToDst(ctx.srcAttr * ctx.attr), _ + _, TripletFields.Src)

      prevRank = rank
      val rPrb = {
        (src: VertexId, id: VertexId) =>
          alpha * delta(src, id)
      }

      rank = rank.outerJoinVertices(rankUpdates) {
        (id, oldRank, msgSumOpt) =>
          rPrb(srcNode, id) + (1.0 - alpha) * msgSumOpt.getOrElse(0.0)
      }.cache()

      rank.edges.foreachPartition(x => {})
      prevRank.vertices.unpersist(false)
      prevRank.edges.unpersist(false)

      i += 1
    }

    val filtered = graph.subgraph(
      vpred = (k, v) => v.isInstanceOf[PatientProperty])
      .collectNeighborIds(EdgeDirection.Out)
      .map(
        r => r._1).collect.toSet

    val top = rank.vertices.filter(
      r => filtered.contains(r._1))
      .takeOrdered(11)(Ordering[Double]
        .reverse.on(
          r => r._2)).map(_._1)

    top.slice(1, top.length).toList
  }
}
