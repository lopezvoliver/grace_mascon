[![Binder](https://mybinder.org/badge_logo.svg)](https://binder.kaust.edu.sa/v2/gh/lopezvoliver/grace_mascon/master?labpath=index.ipynb)

# GRACE mascon linear trend 

This repository contains a notebook to analyze the Gravity Recovery And Climate Experiment (GRACE) original and follow-on missions data over one region. Specifically, the data analyzed is the Center for Space Research (CSR) release 06 mass concentration (mascons) product, [publicly available here](https://www2.csr.utexas.edu/grace/RL06_mascons.html). Acknowledgement/citation should be made to the following reference as well as others mentioned in the link above. 

Save, H., S. Bettadpur, and B.D. Tapley (2016), High resolution CSR GRACE RL05 mascons, J. Geophys. Res. Solid Earth, 121, doi:[10.1002/2016JB013007](http://dx.doi.org/10.1002/2016JB013007).

The notebook [index.ipynb](index.ipynb) [can be opened in binder](https://binder.kaust.edu.sa/v2/gh/lopezvoliver/grace_mascon/master?labpath=index.ipynb). One region of study is already loaded as [a geojson file](Saq.geojson): the Saq aquifer system in Saudi Arabia. The notebook loads the netcdf data and clips to this region. An interactive visualization then allows you to calculate a linear trend between a selected date range. 


![image](https://user-images.githubusercontent.com/14804652/204226749-392d8e29-b2ec-4f07-b517-31c7b6ea1cfd.png)

![image](https://user-images.githubusercontent.com/14804652/204219186-2ee46005-a30f-4f63-9c8a-0972486c608e.png)

