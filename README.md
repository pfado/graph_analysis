# Graph Analysis
This repository contains the code and tools employed for my bachelor thesis in the analysis of graph networks obtained of fMRI.

For some of these scripts, it is necessary to have a available NVIDIA GPU, due to being heavely dependent on the usage of RAPIDS packages, such as cuDF and cuGraph. To see the requitements and installation methods go to [RAPIDS Getting Started](https://rapids.ai/start.html) page. My personal recomendation for local execution is to use either Conda or a docker enviroment and I have not checked the [cloud services](https://docs.rapids.ai/deployment/stable/cloud/#) offered.

Although I used accelerated algorithms in this project, one may try to avoid the necessity for local execution if a suitable GPU is not available by utilizing the NetworkX and Pandas packages. However, be aware that Python execution times for large networks skyrocket.

The parameter analysis scripts, frequency distribution analysis scripts, and IPython notebooks -- for a more visible implementation of the other scripts -- will be the three primary folders that make up this repository. Additionally, there will be two distinct scenarios: one in which we only attempt to acquire the configuration for a certain weight threshold, and another in which we attempt to obtain the configurations using threshold percentages.

## Sections that require improvement:
  
  - When computing the different parameters for the percentages, (if in next projects this is still used), you should try to change how the process of obtaining the distance and efficiency is obtained (maybe, try to compute the biggest and then go erasing the entries from the dataframe obtained when calling the `sssp` function of the nodes that have not a conection with the node that we are analyzing) -> I know this is explained very messy, but if needed, contact me and I'll try to explain it better.
  
  - I use the community function of cuGraph `count_triangles`, that it is the one that limits the max number of edges we can use (8 Million with my GPU).
