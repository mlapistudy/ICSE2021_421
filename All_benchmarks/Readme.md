# README

This folder contains a suite of 360 non-trivial projects that used in our manual study.

We provide data in both excel and csv format.



`Benchmark suite - multi api.csv` contains the projects using multiple ML-APIs, which has already recorded in other csv files. We add an extra `multi-use pattern` column in it to describe the workflow. The details go as follows.

| Multi-use Pattern | #    | Description                                          |
| ----------------- | ---- | ---------------------------------------------------- |
| A                 | 72   | input -> DNN1 -> DNN2 -> output                      |
| B                 | 11   | input -> DNN1 OR DNN2 -> output                      |
| C                 | 26   | input -> DNN1 AND DNN2 -> output                     |
| D                 | 14   | input -> DNN1 -> decide whether -> DNN2 -> output    |
| E                 | 3    | input1 -> DNN1 -> output1; input2-> DNN2 ->  output2 |