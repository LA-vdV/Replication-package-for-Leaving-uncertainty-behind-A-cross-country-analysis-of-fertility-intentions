*----------------------------*
** 		Fit statistics		**
*----------------------------*

frame change default
capture frame drop fitstats
frame create fitstats
frame change fitstats

 
foreach folder in full_sample {  
  	
import delimited "$output/`folder'/fit_statistics.csv", clear
gen st_name = substr(name,1, strpos(name,"_")-1) if strpos(name,"_")!=0
replace st_name = name if strpos(name,"_")==0
replace st_name = proper(st_name)
gen output = "macro" if strpos(name,"macro")!=0 | name =="accuracy"
replace output= substr(name,strpos(name,"_")+1,strlen(name)) if mi(output)

 

replace sample = proper(sample)


table  (sample st_name)  (output) if  st_name!="F1" , statistic(mean statistic)  nototals
 	collect style cell, nformat(%5.3f)
	collect title "Table... "
	collect style header, title(hide)
	collect style row stack, delimiter(`" # "') atdelimiter(`" @ "') bardelimiter(`" | "') binder(`"="') spacer indent length(.) wrapon(word) noabbreviate wrap(.) truncate(tail)
	collect label levels output   macro "Average" yes "Yes" uncertain "Uncertain" no "No", modify
	
 collect export "$tables/table_B1.xlsx"  , replace  

 

** Confusion matrix
*------------------------------

import delimited "$output/`folder'/confusion_matrices.csv", clear
reshape long hat_ , i(sample actual_class) j(outcome) string 
replace outcome = proper(outcome)
label var outcome "Predicted intention"
label var actual_class "Actual intention"

replace sample = proper(sample)
 

table (sample actual ) (outcome), statistic(mean hat)  nototals
	collect style header, title(hide)
	collect style row stack, spacer
	collect preview
	
	
 collect export "$tables/table_B2.xlsx"  , replace  
	
		}
 