*---------------------------------------------------*
*		Permutation feature importance				*
*---------------------------------------------------*


capture program drop labellize 
program define labellize
	syntax varname
	
replace `1' = "Female"  if `1'== "female" 	
replace `1' = "Age"  if `1'== "age"
replace `1' = "Migrant"  if `1'== "migrant"
replace `1' = "Education (own)"  if `1'== "educ_own"
replace `1' = "Employment status"  if `1'== "empl_lv"
replace `1' = "Health"  if `1'== "subj_health"
replace `1' = "Happiness"  if `1'== "happy"
replace `1' = "Trust"  if `1'== "trust"
replace `1' = "Future plan"  if `1'== "future_plan"
replace `1' = "Religiosity"  if `1'== "religious"
replace `1' = "Desire to move"  if `1'== "want_move"

replace `1' = "Partnership status"  if `1'== "partner"
replace `1' = "Age (partner)"  if `1'== "age_partner"
replace `1' = "Education (partner)"  if `1'== "educ_partner"
replace `1' = "Employed (partner)"  if `1'== "empl_partner"

replace `1' = "Number of children"  if `1'== "child_few"
replace `1' = "Below ideal family size" if `1' =="missing_children"
replace `1' = "Earnings"  if `1'== "earnings"
replace `1' = "Owns current residence"  if `1'== "isowner"


replace `1' = "Country"  if `1'== "cn"
replace `1' = "COVID deaths"  if `1'== "std_tv_deaths"
 
end



import delimited "$output\full_sample\permutation_importance.csv", clear
labellize feature






 graph dot (mean) accuracy_mean precision_mean recall_mean, ///
		over(feature, sort(accuracy_mean) descending label(labsize(11-pt)) ) ///
		ytitle(Loss from permutting a variable)  marker(3, msymbol(diamond))  linetype(line) lines(lpattern(dash) lcolor(gs14)) ///
		legend(order(1 "Accuracy" 2 "Balanced Precision" 3 "Balanced Recall") pos(6) r(1) ) ///
		xsize(12) ysize(6) 
		
	
 graph export "$tables/Figure_2.png" , replace
 graph export "$tables/Figure_2.wmf" , replace	