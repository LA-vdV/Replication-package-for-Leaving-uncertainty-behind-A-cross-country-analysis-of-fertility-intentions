*-------------------------------------------------------*
*	  Inspecting the partial dependence functions		*
*-------------------------------------------------------*


frame change default

** Results from young and childless

capture frame drop pdp_young
frame create pdp_young 
frame change pdp_young

import delimited "$output\only_yc\pdp.csv"
ren (no_pdp uncertain_pdp yes_pdp) (no_young uncertain_young yes_young) 

** Results from main sample
capture frame drop pdp_all
frame create pdp_all 
frame change pdp_all

import delimited "$output\full_sample\pdp.csv"
ren (no_pdp uncertain_pdp yes_pdp) (no_all uncertain_all yes_all) 


frlink 1:1 feature1  f1_value , frame(pdp_young) gen(f_young)
frget no uncertain yes , from(f_young) 


** Labels
replace f1_value = "1-Very easily"  		if f1_value == "Very easily"
replace f1_value = "2-Fairly easily"  	 	if f1_value == "Fairly easily"
replace f1_value = "3-Easily"			  	if f1_value == "Easily"
replace f1_value = "4-With some difficulty" if f1_value == "With some difficulty"
replace f1_value = "5-With difficulty"  	if f1_value == "With difficulty"
replace f1_value = "6-With great difficulty" if f1_value == "With great difficulty"

replace f1_value = "1-Definitely not"  		if f1_value == "Definitely not"
replace f1_value = "2-Probably not"  		if f1_value == "Probably not"
replace f1_value = "3-Unsure"  				if f1_value == "Unsure"
replace f1_value = "4-Probably yes"  		if f1_value == "Probably yes"
replace f1_value = "5-Definitely yes"  		if f1_value == "Definitely yes"



 
** Define groupings
gen ind_xs = inlist(feature1, "age", "female" , "migrant" , "happy" , "trust") | ///
			inlist( feature1, "future_plan", "educ_own" ,"subj_health" , "religious") | ///
			inlist(feature1, "empl_lv" , "want_move")

gen part_xs = inlist(feature1, "age_partner", "educ_partner" , "empl_partn") 

gen hh_xs 	= inlist(feature1 , "partner" , "isowner", "missing_children", "child_few", "earnings")

gen macro_xs = inlist(feature1 , "std_tv_deaths" , "cn", "med_home", "med_school", "med_work")
			
gen all_vars = ind_xs+hh_xs + part_xs + macro_xs			

tab all_vars

replace feature1 = "01) Gender"  if feature1== "female" 	
replace feature1 = "02) Age"  if feature1== "age"
replace feature1 = "03) Migrant"  if feature1== "migrant"
replace feature1 = "04) Education (own)"  if feature1== "educ_own"
replace feature1 = "05) Employment status"  if feature1== "empl_lv"
replace feature1 = "06) Health"  if feature1== "subj_health"
replace feature1 = "07) Happiness"  if feature1== "happy"
replace feature1 = "08) Trust"  if feature1== "trust"
replace feature1 = "09) Future plan"  if feature1== "future_plan"
replace feature1 = "10) Religiosity"  if feature1== "religious"
replace feature1 = "11) Desire to move"  if feature1== "want_move"

replace feature1 = "12) Partnership status"  if feature1== "partner"
replace feature1 = "13) Age (partner)"  if feature1== "age_partner"
replace feature1 = "14) Education (partner)"  if feature1== "educ_partner"
replace feature1 = "15) Employed (partner)"  if feature1== "empl_partner"

replace feature1 = "16) Number of children"  if feature1== "child_few"
replace feature1 = "17) Below ideal family size" if feature1 =="missing_children"
replace feature1 = "18) Earnings"  if feature1== "earnings"
replace feature1 = "19) Owns current residence"  if feature1== "isowner"


replace feature1 = "20) Country"  if feature1== "cn"
replace feature1 = "21) COVID deaths"  if feature1== "std_tv_deaths"
replace feature1 = "22) Stay at home" if feature1 =="med_home"
replace feature1 = "23) Work restrictions" if feature1 =="med_work"
replace feature1 = "24) School closures" if feature1 =="med_school"

count
local n_new = `r(N)'+1
set obs  `n_new'

** Adding the average values from the sample
replace feature1 = "00) Average"  	if mi(feature1)
replace f1_value = " "  			if feature1 == "00) Average"
replace yes_all       = 0.242 		if feature1 == "00) Average"
replace uncertain_all = 0.123 		if feature1 == "00) Average"
replace no_all        = 0.634 		if feature1 == "00) Average"
replace yes_young     = 0.453 		if feature1 == "00) Average"
replace uncertain_young = 0.188 	if feature1 == "00) Average"
replace no_young 	    = 0.360 	if feature1 == "00) Average"
 
 capture program drop table_format
program define table_format
	collect style cell, nformat(%5.3f)
	collect title "Table... "
	collect label dim varname "Variable", modify
	collect label dim labels "levels", modify
	collect style header, title(hide)
	collect style row stack, delimiter(`" # "') atdelimiter(`" @ "') bardelimiter(`" | "') binder(`"="') spacer indent length(.) wrapon(word) noabbreviate wrap(.) truncate(tail)
	collect label levels var yes "Yes" uncertain "Uncertain" no "No", modify
	collect label dim var "intention", modify
	collect label levels yc _all "Full sample" _young "Respondents younger than 39 with one or fewer children", modify
	collect notes `"Notes: Table shows partial dependence profiles for variables in the model."'

end

reshape long no uncertain yes , i(feature1 f1_value) j(yc) string

 
table (feature1 f1_value) ( yc var )   if !mi(f1_value)    , statistic(mean yes uncertain no)  nototals
table_format
collect preview
collect export "$tables/Table_1.xlsx" , replace
 

