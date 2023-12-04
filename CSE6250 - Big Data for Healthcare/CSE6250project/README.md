# CSE6250project
Sleep Data Project

Assuming a Debian based Linux Distribution
1. Run update in case this is a new installation.
```
sudo apt update
```
2. Ensure you've installed Java 8/11 for Spark 3.1.1.

On Debian this is very easy with either of these commands:
```
sudo apt install default-jdk
sudo apt install openjdk-11-jdk
```
3. Unzip combined Spark 3.1.1 and Hadoop 3.2 into /opt/spark
4. Set the following environment variables and add them to your system path

PATH, JAVA_HOME, and SPARK_HOME

**Note that JAVA_HOME may have already been added to the path.

**Note that these may need to be added to .bashrc if using WLS2.
```
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin:$JAVA_HOME/bin
```
5. Install Anaconda and restart your terminal, then run 
```
conda update conda
```
to update to version 4.10.0

6. Create a conda pytorch environment based on the included environment.yml file.
```
conda env update -f environment.yml
```
7. Activate the environment with 
```
conda activate pytorch
```
8. Download the code from this repository
```
git clone https://github.gatech.edu/ralbright7/CSE6250project.git .
```
9. cd into the repo and create the following directories
```
mkdir data
mkdir output
mkdir train
mkdir valid
mkdir test
```
10. enter the data directory and download the data from physionet
```
cd data
wget https://www.physionet.org/static/published-projects/sleep-edfx/sleep-edf-database-expanded-1.0.0.zip
unzip sleep-edf-database-expanded-1.0.0.zip
rm sleep-edf-database-expanded-1.0.0.zip
```
11. go back to the code directory
```
cd ../code
```
12. Our Project used the casssette dataset execute the following commands to generate the data transforms. You may need to modify the spark settings to run on whatever system you are running it on. The base system used to generate the transforms was an Intel hexacore I-7 with 64GB of ram.
```
python scala_mapreduce.py -t eeg_psd_welch -s mean
python scala_mapreduce.py -t eeg_psd_welch -s median
python scala_mapreduce.py -t eeg_psd_multitaper -s mean
python scala_mapreduce.py -t eeg_psd_multitaper -s median
python scala_mapreduce.py -t eeg_tfr_morlet -s mean
python scala_mapreduce.py -t eeg_tfr_morlet -s median
python spectograph.py 
```
13. Now that the raw transformations have been generated, it is time to conver them into dataframes for training.
```
python merge_features -f cassette.eeg_psd_welch.mean.pkl
python merge_features -f cassette.eeg_psd_welch.median.pkl
python merge_features -f cassette.eeg_psd_multitaper.mean.pkl
python merge_features -f cassette.eeg_psd_multitaper.median.pkl
python merge_features -f cassette.eeg_tfr_morlet.mean.pkl
python merge_features -f cassette.eeg_tfr_morlet.median.pkl
python merge_features -f cassette.eeg_psd_welch.mean.pkl -f cassette.eeg_tfr_morlet.mean.pkl
python merge_features -f cassette.eeg_psd_welch.median.pkl -f cassette.eeg_tfr_morlet.median.pkl
python merge_features -f cassette.eeg_psd_multitaper.mean.pkl -f cassette.eeg_tfr_morlet.mean.pkl
python merge_features -f cassette.eeg_psd_multitaper.median.pkl -f cassette.eeg_tfr_morlet.median.pkl
```
14. The spectrograph code initially does not trim the wake periods from the beginning and end of each recording session. Since the spectrograph files are per recording per epoch, execute the following script to trim them.
```
python chop_awake_cassette.py
```
15.  Now we are ready to run our models, which can be run using the following command.
```
python train_models.py
```
16. Now run the spectrograph model.  We must pass in a -s command line switch in order for it to separate the images into train, valid, and test directories on the initial pass. Subsequent passes are run without the -s will run on the existing populated directories.
```
python train_spectrograph.py -s
```
17. Experiments were conducting by adding a dropout to the 1d cnn model, and also altering the epochs and batch sizes. This can be done via the -b and -e command line switches.  ie.
```
python train_models.py -b 64 -e 50
python train_spectrograph.py -b 64, -e 50
```
