package edu.gatech.cse6242;

import org.apache.hadoop.fs.Path;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.*;
import org.apache.hadoop.util.*;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import java.io.IOException;
import java.io.*;
import java.util.Iterator;
import java.util.StringTokenizer;


public class Q4 {

  public static class GraphMapper extends Mapper<LongWritable, Text, Text, Text>{  

    @Override
    public void map(LongWritable offset, Text value, Context context) 
      throws IOException, InterruptedException 
    {
      String line = value.toString();
      String[] col = line.split("\t");
      Text col1 = new Text(col[0]);
      Text col2 = new Text(col[1]);
      Text textValue1 = new Text();
      Text textValue2 = new Text();
      String s1 = "1,0";
      textValue1.set(s1);
      //System.out.println("Mapper Key: " + col1);
      //System.out.println("Mapper Value:" + textValue1);
      context.write(col1, textValue1);
      String s2 = "0,1";
      textValue2.set(s2);
      //System.out.println("Mapper Key: " + col2);
      //System.out.println("Mapper Value:" + textValue2);
      context.write(col2, textValue2);

    }
  }
  
  public static class GraphReducer extends Reducer<Text, Text, Text, Text> {

    @Override
    public void reduce(Text key, Iterable<Text> values, Context context) 
      throws IOException, InterruptedException 
    {
      Iterator<Text> i = values.iterator();
      int count = 0;
      while ( i.hasNext() ){
        Text line = (Text)i.next();
        //System.out.println("Debug Key: " + key);
        //System.out.println("Debug Values: " + line);
        String[] col = line.toString().split(",");
        //System.out.println("Debug col1: " + col[0]);
        //System.out.println("Debug col2: " +col[1]);
        count += Integer.parseInt(col[0]);
        count -= Integer.parseInt(col[1]);
      }

      context.write( new Text("" + count), key);
    }
  }

  public static class FinalReducer extends Reducer<Text, Text, Text, Text> {

    @Override
    public void reduce(Text key, Iterable<Text> values, Context context) 
      throws IOException, InterruptedException 
    {

      Iterator<Text> i = values.iterator();
      int count = 0;
      while ( i.hasNext() ){
        Text line = (Text)i.next();
        //System.out.println("Debug Key: " + key);
        //System.out.println("Debug Values: " + line);
        count += 1;
      }

      context.write( key, new Text("" + count));
    }
  }



  public static void main(String[] args) throws Exception {
    Configuration conf = new Configuration();
    Job job = Job.getInstance(conf, "Q4");

    job.setJarByClass(Q4.class);
    job.setMapperClass(GraphMapper.class);
    job.setCombinerClass(GraphReducer.class);
    job.setReducerClass(FinalReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(Text.class);

    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));
    System.exit(job.waitForCompletion(true) ? 0 : 1);
  }
}
