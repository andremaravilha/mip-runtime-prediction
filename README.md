# Prediction of computational runtime for solving MIP problems using Gurobi

> **Contributors:** Yuri Dimitre Dias de Faria<sup>1</sup>, André L. Maravilha<sup>2</sup>  
> <sup>1</sup> *Undergraduate in Computer Engineering - Centro Fed. de Edu. Tecnológica de Minas Gerais ([url](https://www.cefetmg.br/))*  
> <sup>2</sup> *Dept. of Informatics, Management and Design - Centro Fed. de Edu. Tecnológica de Minas Gerais ([url](https://www.cefetmg.br/))*  


## 1. About

Repository with the source code and the results of computational experiments used to build a runtime predictor for solving MIP problems using Gurobi solver.


## 2. How to run this project

Some important comments before building the project:

* This project was developed with Python 3.11 and it uses `gurobipy` (v. 10.0.3), a Gurobi's API for Python. However, no license for Gurobi solver is provided with the code in this repository. Visit Gurobi website ([https://www.gurobi.com/](https://www.gurobi.com/)) to find out how to obtain a license.
* Command in sections below assumes your Python executable is `python` and the Package Installer for Python (pip) is `pip`.
* Besides, it assumes the `venv` module is installed, since it will be used to build the Python Virtual Environment to run the project.

#### 2.2. Create and activate a Python Virtual Environment (venv)

First, you need to clone this repository or download it to your machine. Then, inside the root directory of the project, create a Python Virtual Environment (venv):
```
python -m venv ./venv
```

After that, you need to activate the virtual environment (venv).

In Linux machines, it is usually achieved by running the following command: 
```
source ./venv/bin/activate
```

On Windows:
```
.\venv\Scripts\activate
```

If you want to leave the virtual environment, run:
```
deactivate
```

#### 2.3. Installing dependencies

With your virtual environment installed, you need to install the dependencies required by this project: 
```
pip install -r requirements.txt
```

#### 2.4. Installing dependencies

Now you are ready to run the code! For this, just run the Python script `main.py`:
```
python main.py
```

This script will download the selected MIPLIB 2017 ([https://miplib.zib.de/](https://miplib.zib.de/)) instances to `data/instances` folder and solve them with Gurobi solver. After it is finished, the results will be available in `data/results.csv` file. Besides, Gorobi logs for each instance will be in `data/gurobi_log` folder.
