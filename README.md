# A Replication of Are Machine Learning CloudAPIs Used Correctly

This artifact for our paper “Are Machine Learning Cloud APIs Used Correctly? (#421)” includes both an organized database about ML-API misuses, and tools/checkers we developed. We choose to claim for the Reusable and Available badges, and we hope this artifact can motivate and help future research to further tackle ML API misuses.

The artifact has been published as [a project on Github](https://github.com/mlapistudy/ICSE2021_421).

## What's inside the artifact:

For availability and reusability, we provide an organized database used in our manual studies. In addition, we provide code and data of our tools/checkers and the instructions for setting up working environment.

Below are details of what is included in each part:

### Organized database

The result of TABLE III (manual study part) in our paper can be reproduced by this organized databse. It contains:

1. A suite of 360 non-trivial projects that use Google/Amazon ML APIs, including vision, speech, and language. Located at `All_benchmarks` folder, containing
   1. software project name
   2. GitHub link
   3. exact release number
   4. used API
   5. description
2. A collection of ML-API misuses in these projects (involves 249 projects). Located at `Mis-uses` folder, containing
   1. the exact file and source-code line location of the misuse 
   2. a detailed explanation, including the anti-pattern category and a patch suggestion
3. Test cases to trigger the misuse. Located at `Trigger_misuses` folder.

### Tools/Checkers

The result of TABLE III (auto detection part) and Section VII in our paper can be reproduced by these tools/checker.

They are located in `Tools` folder. Each contains a seperate README file describing more details and instructions.

1. Output mis-interpretation checker (Section VII, first subtitle)
   1. It is a static checker to automatically detect mis-uses of the sentiment-detection API’s output, a type of accuracy bugs discussed in Section IV-B.
2. Asynchronous API call checker (Section VII, second subtitle)
   1. It automatically identifis problems of calling asynchronous APIs in a synchronous, blocking way, a type of performance mis-use discussed in Section V-B.
3. Constant-parameter API call checker (Section VII, third subtitle)
   1. It automatically identifies speech synthesis API calls that use constant inputs, a type of performance mis-use discussed in Section V-D.
4. API wrappers (Section VII, last subtitle)
   1. It wraps cloud APIs to tackle the anti-patterns of missing input validation (Section IV-C), forgetting parallel APIs (Section V-C), misuse of asynchronous APIs (Section V-B), and unnecessarily high-resolution inputs (Section V-E).



## How to obtain paper's result from our tool?

### Manual Study

Our manual study result in Table III could be obtained from `Mis-uses` folder.

In `Mis-uses/ML API misuse list.xlsx`, there are two tabs:

1. Data tab: Contains mis-uses founded in our manual study. It also has a copy in `Mis-uses/ML API misuse list.csv`
2. Analyze tab: it inclues excel formula for computing the mis-use count based on the numbers in the Data tab. The cells for computation are colored with light blue.
   1. Column X: # of types of API misuses in each applications
   2. Row 255: # of problematic projects for each anti-pattern
   3. Row 259-275: A copy of Table III

### Auto Detection

Our auto detection result in TABLE III and Section VII could be obtained from `Tools` folder. Please follow `REQUIREMENTS.md` to set up environment and instructions in  `Tools` folder to reproduce the result.

These tools are applied to public GitHub repositories using ML cloud APIs. The result obtained by our tool may differ between two execution, as GitHub repositories might be created, updated, and deleted during these process. For the unchanged repositores, our tools will always provide same result. The result in our paper are obtained right before paper submission (August 2020). 



## What to do with the artifact and how?

One can use the code and data to check the statistic details and reproduce the experiments in our paper.

We put detailed instructions for setting up the environment in the INSTALL file. The instructions for tools/checkers are in the README file in their subfolders under `Tools`.