# README

This folder contains a collection of ML-API misuses in 360 applications used in our manual study.

We provide data in both excel and csv format.



In `Mis-uses/ML API misuse list.xlsx`, there are two tabs:

1. Data tab: Contains mis-uses founded in our manual study. It also has a copy in `Mis-uses/ML API misuse list.csv`
   1. The numbers in data tab represent number of misuses in applications, counted by code locations.
   2. Google Vision have `batch_annotate_images` and `annotate_images` APIs for general API call. To make description clear, we use the exact function instead, e.g.`label_detection`.
   3. In the **code line** column, each occurence of mis-use is seperated by a semicolon, in the order that they are presented in the same row from left to right. If multiple code lines are needed to better showcase the underlying issue, they are wrapped in one parentheses.
2. Analyze tab: it inclues excel formula for computing the mis-use count based on the numbers in the Data tab. The cells for computation are colored with light blue.
   1. Column X: # of types of API misuses in each applications
   2. Row 255: # of problematic projects for each anti-pattern
   3. Row 259-275: A copy of Table III

### 