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
      context.write(col1, textValue1);
      String s2 = "0,1";
      textValue2.set(s2);
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
        String[] col = line.toString().split(",");
        count += Integer.parseInt(col[0]);
        count -= Integer.parseInt(col[1]);
      }

      context.write(key, new Text("" + count));
    }
  }

    public static class FinalMapper extends Mapper<LongWritable, Text, Text, Text>{  

    @Override
    public void map(LongWritable offset, Text value, Context context) 
      throws IOException, InterruptedException 
    {
      String line = value.toString();
      String[] col = line.split("\t");
      Text col1 = new Text(col[0]);
      Text col2 = new Text(col[1]);
      context.write(col2, col1);
    }
  }

  public static class FinalReducer extends Reducer<Text, Text, Text, Text> {

    @Override
    public void reduce(Text key, Iterable<Text> values, Context context) 
      throws IOException, InterruptedException 
    {
      Integer k = Integer.parseInt(key.toString());
      Iterator<Text> i = values.iterator();
      int count = 0;
      while ( i.hasNext() ){
        Text line = (Text)i.next();
        count += 1;
      }
      context.write( key, new Text("" + count));
    }
  }


  public static void main(String[] args) throws Exception {
    Configuration conf = new Configuration();
    Path outputPath=new Path("opt");
    Job job = Job.getInstance(conf, "Q4");

    job.setJarByClass(Q4.class);
    job.setMapperClass(GraphMapper.class);
    job.setCombinerClass(GraphReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(Text.class);
    
    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, outputPath);
    job.waitForCompletion(true);

    Job job2 = Job.getInstance(conf, "Q4");

    job2.setJarByClass(Q4.class);
    job2.setMapperClass(FinalMapper.class);
    job2.setReducerClass(FinalReducer.class);
    job2.setOutputKeyClass(Text.class);
    job2.setOutputValueClass(Text.class);

    FileInputFormat.addInputPath(job2, outputPath);
    FileOutputFormat.setOutputPath(job2, new Path(args[1]));

    job2.waitForCompletion(true);

    outputPath.getFileSystem(conf).delete(outputPath);
    System.exit(job2.waitForCompletion(true) ? 0 : 1);
  }
}