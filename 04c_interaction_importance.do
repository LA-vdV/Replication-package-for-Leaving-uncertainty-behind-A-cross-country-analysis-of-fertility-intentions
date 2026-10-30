*---------------------------------------------------*
*		Identifying relevant interactions			*
*---------------------------------------------------*



import delimited "$output/full_sample/pdp_2d.csv", clear
 
 
gen concat = feature1 + "&" + feature2

gen imp_yes = .
gen imp_no = .
gen imp_unc = .
 
quiet levelsof concat , local(ll)
foreach l in `ll' {
	mkmat f1_idx f2_idx pdp_no pdp_uncertain pdp_yes if concat =="`l'", matrix(m1)
	
	extract_info m1 , coln(3)
		local no `r(if)'
	quiet replace imp_no = `r(if)' if  concat =="`l'"
		
	extract_info m1 , coln(4)
		local uncertain `r(if)'
	quiet replace imp_unc = `r(if)' if  concat =="`l'"
	
	extract_info m1 , coln(5)
		local yes `r(if)'
	quiet replace imp_yes = `r(if)' if  concat =="`l'"
	
}

 
collapse (mean) imp_* (first) feature1 feature2 , by(concat)

expand 2 , gen(new)
replace feature2 = substr(concat, 1, strpos(concat, "&")-1) if new== 1
replace feature1 = substr(concat, strpos(concat, "&")+1,.) if new== 1
  
replace feature1 = "01) Female"  if feature1== "female" 	
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

encode feature1, gen(f1_n)
 

* Figure 3
twoway (scatter f1_n imp_unc  , msize(small) mcolor(gs9) ) ///
		 , ytitle(" ") ylabel(#24, valuelabel) ysca(reverse)  ///
		xtitle("Interaction strength")  title("Uncertain fertility intentions") ///
		yline(11.5)  yline(15.5)  yline(19.5) name(gr_unc, replace) legend(off)

graph export "$tables/Figure_3.png" , replace
graph export "$tables/Figure_3.wmf" , replace	
 
* Figure A5 
scatter f1_n imp_yes  , ytitle(" ") ylabel(#24, valuelabel) ysca(reverse) msize(small)  mcolor(gs9)  ///
		xtitle("Interaction strength") yline(11.5)  yline(15.5)    yline(19.5) title("Positive fertility intentions")  name(gr_yes, replace)

graph export "$tables/Figure_A5.png" , replace
graph export "$tables/Figure_A5.wmf" , replace	
		
		

 

 