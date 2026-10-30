*----------------------------*
** 		Random Forest		**
*----------------------------*

/* 
The estimation of random forests is done using Python, and it can be ran 
independently.

There are three sets of files
(1) model_configs/... .yaml : These YAML files determine which specifications
	will be run (variables, and samples) and where results will be stored
	We include two models: 
	 a) full_sample (for the main sample used in the analysis)
	 b) only_yc (for the subsample of young individuals with at most one child)
	 -- used only in Table 1 --
	
(2) config_utils and data_processor: read the configurations from YAML into Python
and pre-processes the data to implement the right sample.

(3) Estimation files: rf_pipeline, rf_evaluation, rf_interpretation are the responsibles
for the main analysis. 

*/


python script rf_pipeline.py, args("model_configs\full_sample.yaml") 
* Searches for the best hyperparameters and estimates the random forests
* The model is stored and reused by subsequent files

 python script rf_evaluation.py, args("model_configs\full_sample.yaml") 
* Evaluates the quality of the model. It produces the files required by 
* 04_fitstats_tables, 04_importance_onevar

python script rf_interpretation.py, args("model_configs\full_sample.yaml") 
* Uses the model to estimate partial dependence functions and two-dimensional 
* partial dependence functions. The outcome is used by the files 04_table_pdp
* 04_interaction_importance , 04_interaction_example



python script rf_pipeline.py, args("model_configs\only_yc.yaml") 
*python script rf_evaluation.py, args("model_configs\only_yc.yaml") 
python script rf_interpretation.py, args("model_configs\only_yc.yaml") 

** Notice that 04_table_pdp requires estimating the two configurations.


