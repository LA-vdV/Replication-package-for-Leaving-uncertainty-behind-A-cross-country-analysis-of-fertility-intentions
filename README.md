# Replication package for Leaving uncertainty behind

 

The code allows replicating the results published in *Journal of Demographic Research*. 

All code is run from Stata, though it requires Python to estimate the ML model. Below we detail the different files

## Components

### Configuration Files

- **`model_configs/*.yaml`** - Configuration files for different models. Currently it includes two different configurations: base, and young with fewer than two children.


### Core Pipeline Files

#### Stata
1. **`00_paths.do`** - Set up the environment, download required Stata dependencies, and additional user-written progams. It should be modified by the user to fit its needs

2. **`01a_covid.do`** - Cleans Covid data from WHO. Data should be acquired independently by the user and stored in an adequate folder. Two variables are computed: standardized number of deaths, and time varying standardized number of deaths. 

3. **`01b_data_cleaning.do`** - Harmonizes and merges GGS data for the countries used in the analysis. It creates data_ready2, which is used in subsequent analysis. 

4. **`02_descriptives`** -Creates descriptive statistics for the sample used in the paper. 
     - *Input*: data_ready2 
     - *Output*: `Figure_1.png`, `table_A1.xlsx`,`table_A2.xlsx`, `Figure_A1.png`.

5. **`03_random_forests.do`** - Executes Python code from Stata. (see below for more information)

6. **`04a_importance_onevar`** Creates figure with importance measures for each variable
    - *Input*:  `permutation_importance.csv`
    - *Output*: `Figure_2.png`

7. **`04b_table_pdp`** Creates table with the partial dependence profile. It combines the output of two estimations (full sample, and young with less than two children)
    - *Input*:  `only_yc\pdp.csv`; `full_sample\pdp.csv`
    - *Output*: `Table_1.xslx`


8. **`04c_interaction_importance.do`** It computes the importance of interactions using two-way Partial Dependence Profiles. It prints the results to two figures. It currently runs only the full sample results
    - *Input*:  `full_sample\pdp2.csv`
    - *Output*: `Figure_3.png`; `Figure_A5.png`

9. **`04d_interaction_example.do`** It produces figures displaying the importance of specific interactions for different outcomes. 
    - *Input*:  `full_sample\pdp2.csv`
    - *Output*: `Figure_A2.png`; `Figure_A3.png`; `Figure_A4.png` ; `Figure_A6_pa.png`  ; `Figure_A6_pb.png` ; `Figure_A6_pc.png`

10. **`04e_fitstats_tables.do`**- Produces nice tables from the fitstatistics files 
    - *Input*:  `full_sample\fit_statistics.csv`
    - *Output*: `table_B1.xlsx`;`table_B2.xlsx`



#### Python
1. **`rf_pipeline.py`** - Model training with hyperparameter tuning
    - Loads and preprocesses data according to config
    - Applies sample filters (age, partner status, etc.)
    - Runs hyperparameter tuning with specified parameters
    - Trains final model with best hyperparameters
    - Saves model and all artifacts




2. **`rf_evaluation.py`** - Model evaluation and quality assessment  
- *Output*: `confusion_matrices.csv` ;  `fit_statistics.csv` ; `permutation_importance.csv` 

3. **`rf_interpretation.py`** - Partial dependence functions and interaction analysis
-*Output*: `pdp.csv`; `pdp_2d.csv` 



