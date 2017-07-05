# Anomaly Detection 

This is an implementation of the coding challenge for Insight Data Engineering Fellows Program.
The original problem is here: https://github.com/InsightDataScience/anomaly_detection

## Summary

Implement of a social network where users can add/delete friends and making purchases on an e-commerce platform. It takes two logs of the entire network events - 1. batch_log for building the state of the network and 2. stream_log to simulate and determine whether a purchase is anamalous. If caluclation in real-time that purchases are anomalous, it should be flagged and logged into the flagged_purchase.json file. As events from both files process through, the friends (socail) network and the purchase history of users should be updated.

A purchase is anomalous when the purchase amount is more than 3 standard deviation from the mean of the last `T` purchases in user's `D`th degree network. `D` should not be hardcoded and be flexible, and will be at least `1` and `T` shouldn't be hardcoded as well, and will be at least `2`.

`D`: The number of degrees that defines a user's friends(social) network
`T`: The number of consecutive purchases made by user's friends network (not including the user's own purchases)


## How to run this code

Clone the repo and run `./run.sh` inside the anomaly_detection directory. This runs the code using the files `batch_log.json` and `stream_log.json` in the input_log directory as the input batch and stream files, respectively. It writes the output to the file `flagged_purchases.json` in the output_log directory.


The code is written and tested in Python 2.7. It requires the `json` module.


The python files contains 2 files. 

### File 1: process_classes

It defines class User_Network and class User. The class User_Network has attributes such as add batch event, add streaming event, add purchase, add friends, remove friends. 

### File 2: anomaly_detection

It includs the main function to determine the anomal purchase. 

## Environment & Dependencies
- Code run on python 2.7

The following Python libraries & packages are used:
- sys
- json
- time
- numpy
- heapq
- collections

## Results
The test results show it works when D or T changes. Higher degree requires longer running time.