*---------------------------------------*
*		Descriptive statistics			*
*---------------------------------------*



use ../replication_data/data_ready2 ,clear

drop if eu_code == "SE"


*** TABLE A1: How different restrictions affect the sample size
*-----------------------------------------------------------------

gen cond1 = 1
gen cond2 = age_broad
gen cond3 = age_broad & inlist(partner,1,2) & same_sex_partner ==0
gen cond4 = cond3 & has_fer
gen cond5 = cond4 & has_demo

table country , statistic(total cond1 cond2 cond3 cond4 cond5)   nototal
collect style header, title(hide)
collect label levels var cond1 "All" cond2 "20<=age<=49" cond3 "with partner" cond4 "Fertility intentions" cond5 "Basic demographics" 
collect preview
collect export "$tables/table_A1.xlsx", replace


*** FIGURE 1 Fertility intentions
*-----------------------------------------------
gen fem_string = "F"*(female==1) + "M"*(female==0)
 tab fer_short, gen(d) 
 graph bar (mean) d1 d2 d3  if age_broad ==1 & inlist(partner,1,2) & has_fer & has_demo & same_sex_partner ==0 ///
			& inlist(country, "Austria" , "Croatia", "Czechia", "Denmark" , "Estonia") , ///
		over(fem_string)  over(country) stack ///
	legend(r(1) order (3 "Definitely or probably yes" 2 "Unsure" 1 "Definitely or probably not") pos(6) ) ///
	 blabel(bar, color(black) size(vsmall) position(inside) format(%4.2f))  ///
	 bar(1, fcolor(gs15) lcolor(black) fintensity(inten100)) bar(2, fcolor(gs12) lcolor(black) fintensity(inten100)) ///
	 bar(3, fcolor(gs9) lcolor(black) fintensity(inten100)) xsize(12)  name(gr_top,replace)

graph bar (mean) d1 d2 d3  if age_broad ==1 & inlist(partner,1,2) & has_fer & has_demo & same_sex_partner ==0 ///
			& inlist(country, "Finland" , "Germany", "Netherlands", "Norway" , "United Kingdom") , ///
		over(fem_string)  over(country) stack ///
	legend(r(1) order (3 "Definitely or probably yes" 2 "Unsure" 1 "Definitely or probably not") pos(6) ) ///
	 blabel(bar, color(black) size(vsmall) position(inside) format(%4.2f))  ///
	 bar(1, fcolor(gs15) lcolor(black) fintensity(inten100)) bar(2, fcolor(gs12) lcolor(black) fintensity(inten100)) ///
	 bar(3, fcolor(gs9) lcolor(black) fintensity(inten100)) xsize(12) 	name(gr_low,replace)
 
	 
grc1leg gr_top gr_low, c(1) 	name(gr_comb, replace) 
graph di gr_comb, xsize(6)

graph export "$tables/Figure_1.png", replace as(png)
graph export "$tables/Figure_1.wmf", replace as(wmf)


** Values for Table 1
** They are hardcoded in the file table_pdp.do
tab fer_short if cond5==1
tab fer_short if cond5==1 & inrange(age, 20, 39) & inlist(child_few,0,1)


* Descriptive statistics: TABLE A2
*---------------------------------------------------

keep if age_broad &  has_demo & has_fer & same_sex_partner ==0   & inlist(partner,1,2)

capture drop mi_age_partner
gen mi_age_partner =  (mi(age_partner) | age_partner<15) *100
label var mi_age_partner "(proportion missing)"

local vars1 "female migrant educ_own child_few subj_health religious empl_lv earnings happy trust future_plan isowner want_move  partner"
quiet table (var) (fer_short), statistic(mean age ) statistic(sd age) /// 
						   statistic(fvpercent `vars1') ///
						 statistic(mean age_partner ) statistic(sd age_partner) ///
						 						 statistic(mean mi_age_partner) ///
						   statistic(fvpercent  educ_partner empl_partn) ///
						   statistic(fvpercent countryn) /// 
						 statistic(mean std_tv_deaths ) statistic(sd std_tv_deaths) ///
						  nformat(%6.2f mean sd)  
collect style header result, level(hide)
collect style row stack, nobinder spacer
collect style cell result[sd], sformat("(%s)")
collect preview

collect export "$tables/table_A2.xlsx" , replace


* Figure A1: Covid situation at time of the interview
*----------------------------------------------------------------


use  ../replication_data/int_dates , clear
merge m:1 eu_code month_date using ../replication_data/data_covid


set scheme burd
gen std2_deaths = std_deaths +1
 gen insample = 7*(ones==1)
levelsof eu_code , local(cc) 
foreach c in `cc'{
 

 
 twoway ///
	(bar insample month_date , fcolor(gs13 ) lcolor(none)) ///
	(line std2_deaths month_date  , lwidth(thick) sort) /// 
	if eu_code =="`c'" ///
	, ylabel(0(1.5)6.5) legend(r(1) pos(6) order(1 "Interview dates" 2 "Deaths") ) ///
	xtitle("Date") title("`c'") ytitle("Std(deaths) +1 ") ///
	xlabel(720 "2020" 732 "2021" 744 "2022" 756 "2023" 768 "2024" 780 "2025") ///
	name(gr_`c' , replace)
	
	
} 
  
 grc1leg gr_AT gr_CZ gr_DE gr_DK gr_EE gr_FI gr_UK gr_HR gr_NL gr_NO , r(2) ///
		name(gr_comb, replace)
 
graph di gr_comb , xsize(6)		
graph export "$tables/Figure_A1.wmf", as(wmf) replace
graph export "$tables/Figure_A1.png", as(png) replace 
