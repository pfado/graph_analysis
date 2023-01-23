# Graph Analysis
This repository contains the code and tools employed for my bachelor thesis in the analysis of graph networks obtained of fMRI.

For some of these scripts, it is necessary to have a available NVIDIA GPU, due to being heavely dependent on the usage of RAPIDS packages, such as cuDF and cuGraph. To see the requitements and installation methods go to [RAPIDS Getting Started](https://rapids.ai/start.html) page. My personal recomendation for local execution is to use either Conda or a docker enviroment and I have not checked the [cloud services](https://docs.rapids.ai/deployment/stable/cloud/#) offered.

While in this project I made use of accelerated algorithms using this toolkit, one could use the NetworkX and Pandas libraries to try and circuvent the need for local execution when a fitting GPU is not available, but be wary that execution times using Python go through the roof for big networks
