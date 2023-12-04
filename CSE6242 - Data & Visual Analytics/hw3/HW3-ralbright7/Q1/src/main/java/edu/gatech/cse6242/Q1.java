package edu.gatech.cse6242;

import org.apache.hadoop.fs.Path;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.*;
import org.apache.hadoop.util.*;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import java.io.*;

public class Q1 {

  public static class GraphMapper extends Mapper<LongWritable, Text, Text, Text> {

    Text textKey = new Text();
    Text textValue = new Text();

    @Override
    public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
      String line = value.toString();
      String[] col = line.split("\t");
      String k = col[0];
      String v = col[1] + "," + col[2];
      textKey.set(k);
      textValue.set(v);
      context.write(textKey, textValue);
    }
  }

  public static class GraphReducer extends Reducer<Text, Text, Text, Text> {
    Text textValue = new Text();

    @Override
    public void reduce(Text key, Iterable<Text> values, Context context) 
      throws IOException, InterruptedException 
    {
      int currMax = 0;
      int currNode = 0;
      for (Text value : values) {
        String line = value.toString();
        String[] col = line.split(",");
        int t = Integer.parseInt(col[0]);
        int w = Integer.parseInt(col[1]);
        if(w > currMax) 
        {
          currMax = w;
          currNode = t;
        }
        if(w == currMax)
        {
          if(t < currNode)
          {
            currNode = t;
          }
        }
      }
      textValue.set(currNode + "," + currMax);
      context.write(key, textValue);
    }
  }

  public static void main(String[] args) throws Exception {
    Configuration conf = new Configuration();
    Job job = Job.getInstance(conf, "Q1");

    job.setJarByClass(Q1.class);
    job.setMapperClass(GraphMapper.class);
    job.setCombinerClass(GraphReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(Text.class);

    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));
    System.exit(job.waitForCompletion(true) ? 0 : 1);
  }
}
