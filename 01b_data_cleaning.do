*----------------------------------------*
*	Data cleaning 
*-----------------------------------------*


** Country-specific codes are hard-coded.

global databases : dir "$data_raw" files "GGSII_*.dta"

 
foreach data in $databases {

tokenize "`data'" , parse("_")
local name = proper("`5'")

** Load the data
use "$data_raw/`data'" , clear
	


** Data cleaning

** Data characteristics
gen eu_code = upper("`name'")
gen year    = intdatey
gen month 	= intdatem

** Fertility intentions
recode fer14 (1/2 = 1 "Definitely or probably not" ) ///
		(3=2 "Unsure") (4/5=3 "Probably of definitely yes") (6=.) , gen(fer_short) 

if "`name'" =="Sw" {
recode fer14_2901 (1/2 = 1 "Definitely or probably not" ) /// (3=2 "Unsure") middle is ommited
		 (4/5=3 "Probably of definitely yes") (6=.) , gen(fer_swe) 
		}
		
** Demographic characteristics
gen age = intdatey- dem02y 
gen female =  dem01 ==2 if  dem01<=2
gen migrant = 0
capture replace migrant = dem03==2						// not in UK
capture replace migrant = 1 if dem04a ==4305 & eu_code =="UK"	

recode dem07isced (0/2=1 "1-Primary") (3/4=2 "2-High-School") (5/6= 3 "3-Bachelor") (7/8=4 "4-More than BA") (1401=.) , gen(educ_own)
label var educ_own "Education (own)"

** Household Composition
gen has_partner = dem21  == 1 if !mi(dem21)
gen is_married  = dem28a == 1 if !mi(dem21) & !mi(dem28a)
gen liv_partner = dem30a == 1 if !mi(dem21) & !mi(dem30a)

gen partner = has_partner
replace partner = 2 if is_married == 1

label define partner 0 "0-Single" 1 "1-Partner" 2 "2-Married" , modify
label val partner partner
label var partner "Partnership status"

recode dem25isced (0/2=1 "1-Primary") (3/4=2 "2-High-School") (5/6= 3 "3-Bachelor") (7/8=4 "4-More than BA") (1401=.) , gen(educ_partner)
 

gen age_partner = intdatey- dem22y
replace age_partner =. if age_partner<0 | age_partner>100

gen same_sex_partner = dem23 == dem01 &  !mi(dem23, dem01)


gen ever_same_sex  = same_sex_partner
quiet lookfor lhi17
foreach var of varlist `r(varlist)'{
	replace ever_same_sex = 1 if `var' == 1
}

* Existing children
gen n_children_current     = dem42 if !mi(dem42)
replace n_children_current = 0     if dem41== 2 & mi(n_children_current)
replace n_children_current = 0     if has_partner == 0 

gen any_children_current = dem41 ==1 if !mi(dem41)

gen n_children_previous = 0 

quiet lookfor lhi08  // lhi10
foreach var of varlist `r(varlist)' {
	replace n_children_previous = n_children_previous + `var' if !missing(`var')
}

replace n_children_previous = lhi19 if lhi18==1 & !mi(lhi19)

gen total_children     = n_children_current + n_children_previous

if !inlist("`name'", "De"){
	replace total_children = lhi21 if lhi20==2 & !mi(lhi21) 
 }

recode total_children (3/30= 3) , gen(child_few)

gen missing_children = fer16b > (n_children_current + n_children_previous) if !mi(fer16b)


** Housing
clonevar housing_status = dem11
replace housing_status = 3 if inlist(dem11 , 3 , 4, 2801 ) 
replace housing_status = 3 if mi(dem11) 
replace housing_status = 1 if inlist(dem11 , 4301, 4302) & eu_code =="UK"
replace housing_status = 2 if inlist(dem11 , 4303, 4304) & eu_code =="UK"

recode dem12 (0/4 =1 "1-Dissatisfied") (5=2 "2-Moderately") (6/10 = 3 "3-Satisfied")   ///
		, gen(housing_satisfaction)
 

gen isowner = housing_status == 1 if !mi(dem11)

** Employment 

recode dem06 (1 6 8 11 = 3 "3-Inactive") /// student/training, retired, homemaker, ill or disabled
			(2/4 7     = 1 "1-Working") /// Wage, self, helping family, military
			(5 12  =2 "2-Unemployed")   /// Unemployed, other
			(9/10 =4 "4-Leave") ,      /// On maternity / parental leave
		gen(empl_lv)

replace empl_lv	 = 1 if wrk02==1 & empl_lv!=4
replace empl_lv	 = 2 if wrk02==2 & (empl_lv == 3 | empl_lv ==.) 	
replace empl_lv	 = 3 if wrk02==3 & (empl_lv == 2 | empl_lv ==.) 
		
capture recode wrk01 (0/4=1 "1-Not at all") (5=2 "2-Average" ) (6/10=3 "3-Satisfied")  , gen(emp_sat)

clonevar earnings = inc03 // can make ends meet
	
** Satisfaction 
gen satis_life  = wel01>7 if !mi(wel01)
recode wel01 (0/7 = 1 "1-Dissatisfied") (8 = 2 "2-Median") (9/10 =3 "3-Satisfied")   , gen(life_sat)


** Health
recode wel02 (1=1 "1-Very good") (2=2 "2-Good" ) (3=3 "3-Fair") (4/5=4 "4-Bad")   , gen(subj_health)

gen person_weight = wel06 
gen person_height = wel07

gen happy       = wel08>7 if !mi(wel08)


** Attitudes (social resources)
clonevar trust = att01
capture label copy att01 trust
capture label copy ATT01 trust

label val trust trust

recode att02 (0/2 2901 = 1 "1-I plan" ) (3/4 2902 = 2 "2-Somehow" ) (5/6 2903 =3 "3-Neither nor" ) ///
			 (7/8 2904 = 4 "4-Rather not") (9/10  2905= 5 "5-Take each day")   , gen(future_plan)
label var future_plan "Future plan"


recode att10 (0/4=1 "1-No") (5=2 "2-Intermediate" ) (6/10=3 "3-Yes")  , gen(religious) 
label var religious "Religiosity"


** Partner
recode wrk32 (2 3 = 0 "2-Not employed") (1 = 1 "1-Work")   , gen(empl_partner)
label var empl_partner "Employment (partner)"

** Difficulties
gen moved_nonvol = inlist(dem18, 3 , 4 , 5, 7 )  // Family, work, financial, health 
clonevar want_move = dem19
capture  label copy dem19 want_move , replace
capture   label copy DEM19 want_move , replace
capture clonevar debt = inc05
capture gen debt = .

clonevar unstable_job = wrk16a
if !inlist("`name'", "Uk") clonevar bad_job = wrk16b
if inlist("`name'", "Uk") gen bad_job = .



drop if mi(month)

save ../replication_data/GGSII_`name' , replace
}

clear


cd ../replication_data 

global data			"eu_code year month"
global yvar 		"fer14 fer_short" 
global demog        "female age migrant educ_own partner child_few total_children  housing_status isowner" 
global partner		"has_partner same_sex_partner ever_same_sex empl_partner educ_partner age_partner"
global lmvars	 	"empl_lv earnings unstable_job bad_job"
global attitudes	"happy trust religious future_plan  subj_health"
global difficult  	"moved_nonvol want_move bad_job unstable_job missing_children"


global files: dir "." files "GGS*.dta"
clear
quiet append using $files ,   keep($data $yvar $demog $partner $lmvars $attitudes $difficult  )

cd "$code"

** Sample restrictions
*------------------------

gen age_narrow  = inrange(age, 25, 44)
gen age_broad   = inrange(age, 20, 49)

gen month_date  = ym(year, month)
format month_date %tm

gen has_fer      = !missing(fer_short)
gen full_partner = has_partner & (inrange(age_partner, 20,49) | mi(age_partner)) & same_sex_partner ==0
gen has_demo     = !missing(age, female, migrant, educ_own, partner, housing_status, total_children)
gen has_job  	 = empl_lv==1 & !mi(unstable_job)

replace eu_code ="SE" if eu_code =="SW"

encode eu_code, gen(cn)
label var cn "Country"

merge m:1 eu_code month_date using ../replication_data/data_covid
drop if _merge==2
drop _merge

  
gen country = "Czechia"
replace country = "Austria" 		if eu_code =="AT"
replace country = "Germany" 		if eu_code =="DE"
replace country = "Denmark" 		if eu_code =="DK"
replace country = "Estonia" 		if eu_code =="EE"
replace country = "Finland"      	if eu_code =="FI"
replace country = "Croatia" 	  	if eu_code =="HR"
replace country = "Netherlands"   	if eu_code =="NL"
replace country = "Norway"        	if eu_code =="NO"
replace country = "United Kingdom" 	if eu_code =="UK"

encode country, gen(countryn)

** Variable Labels
label var fer_short 	"Fertility intentions"
label var age 			"Age (own)"
label var migrant 		"Migrant origin"
label var female 		"Gender"
label var educ_own  	"Education (own)"
label var empl_lv 		"Employment status"
label var subj_health 	"Health status (subjective)"
label var isowner		"Owns current dwelling"
label var child_few   	"Number of children"
label var religious   	"Religiosity"
label var subj_health 	"Subjective health"
label var future_plan 	"Future plan" 
label var happy  		"Happiness" 
 
label var partner		"Partnership status"
label var educ_partner  "Education (partner)"
label var age_partner   "Age (partner)"
label var empl_partner  "Employed (partner)"

label var std_deaths 	"Covid deaths (Standardized)"
label var std_tv_deaths "Covid deaths (Standardized, time varying)"
label var countryn		"Country"


** Labels for different levels

label define fer_short 1 "No" 2 "Uncertain" 3 "Yes" , modify


label define yesno 0 "2-No" 1 "1-Yes"	
label val migrant isowner happy bad_job unstable_job missing_children yesno 

label define fem 0 "1-Men" 1 "2-Women"
label val fem fem

label def  child_few 0 "Childless" 1 "One"  2 "Two" 3 "Three or more"   , modify
label val  child_few child_few 


save ../replication_data/data_ready2, replace
 
gen ones=1
collapse (mean) ones, by(month_date eu_code) 
save ../replication_data/int_dates , replace
 

exit
