# README

This artifact for our paper “Are Machine Learning Cloud APIs Used Correctly? (#421)” includes both an organized database about ML-API misuses, and tools/checkers we developed. We choose to claim for the Reusable and Available badges, and we hope this artifact can motivate and help future research to further tackle ML API misuses.

The artifact has been published as [a project on Github](https://github.com/mlapistudy/ICSE2021_421).

## What's inside the artifact:

Inside the artifact, we provide an organized database used in our manual studies for availability. In addition, for reusability, we provide code and data of our tools/checkers and the instructions for setting up environment.

Below are details of what is included in each part:

### Organized database (for availability)

1. A suite of 360 non-trivial projects that use Google/Amazon ML APIs, including vision, speech, and language. Located at `All_benchmarks` folder, containing
   1. software project name
   2. GitHub link
   3. exact release number
   4. used API
   5. description
2. A collections 247 ML-API misuses in these projects. Located at `Mis-uses` folder, containing
   1. the exact file and source-code line location of the misuse 
   2. a detailed explanation, including the anti-pattern category and a patch suggestion
3. Test cases to trigger the misuse. Located at `Trigger_misuses` folder.

### Tools/Checkers (reusability)

Located in `Tools` folder. Each contains a seperate README file describing more details and instructions.

1. Output mis-interpretation checker
2. Asynchronous API call checker
3. Constant-parameter API call checker
4. API wrappers



## What to do with the artifact and how?

One can use the code and data to check the statistic details and reproduce the experiments in our paper.

We put detailed instructions for setting up the environment in the INSTALL file. The instructions for tools/checkers are in the README file in their subfolders under `Tools`.