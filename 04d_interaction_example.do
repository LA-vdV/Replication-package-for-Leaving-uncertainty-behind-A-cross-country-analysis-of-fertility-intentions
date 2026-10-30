*-------------------------------------------*
*		Inspecting interactions				*
*-------------------------------------------*

set scheme burd
import delimited "$output\full_sample\pdp_2d.csv", clear
 
* Figure A2 
graph bar (asis) pdp_uncertain if feature2=="missing_children" & feature1 =="partner", ///
	over(f1_value, label(nolabel) ) over(f2_value ) asyvars legend(order(1 "Partner" 2 "Married") ) ///
	title("Uncertain fertility intentions") name(gr1, replace) ///
	bar(1, fcolor(gs12) lcolor(black))  bar(2, fcolor(gs5) lcolor(black)) ///
		yline(0.14, lcolor(gs12) lpattern(solid)) yline(0.1, lcolor(gs6))   ///
		note("Below ideal family size" ,ring(2) pos(6) size(medlarge)) 
		
graph export "$tables/Figure_A2.wmf", replace as(wmf)	
graph export "$tables/Figure_A2.png", replace as(png)
	
	
* Figure A3	
graph bar (asis) pdp_uncertain if feature2=="cn" & feature1 =="partner", ///
	over(f1_value, label(nolabel) ) over(f2_value) asyvars legend(order(1 "Partner" 2 "Married") ) ///
	title("Uncertain fertility intentions") name(gr1, replace) ///
	bar(1, fcolor(gs12) lcolor(black))  bar(2, fcolor(gs5) lcolor(black)) 	 xsize(6)  ///
	yline(0.14, lcolor(gs12) lpattern(solid)) yline(0.1, lcolor(gs6)) ///
	note("Country" ,ring(2) pos(6) size(medlarge)) 
	
graph export "$tables/Figure_A3.wmf", replace as(wmf)
graph export "$tables/Figure_A3.png", replace	as(png)



** Interactions with Pandemic Intensity
*----------------------------------------------------

gen deaths = real(f2_value) if feature2 =="std_tv_deaths" 
replace deaths =  real(f1_value) if feature1 =="std_tv_deaths" 


* Figure A4
twoway 	(connect pdp_unc deaths if f2_value =="24")  ///
		(connect pdp_unc deaths if f2_value =="28") ///
		(connect pdp_unc deaths if f2_value =="32") ///
		(connect pdp_unc deaths if f2_value =="36")  ///
		(connect pdp_unc deaths if f2_value =="40")  ///
		(connect pdp_unc deaths if f2_value =="48")  ///
		if feature1 =="std_tv_deaths" & feature2 == "age_partner" 	   , ///
		legend(order(- "Age partner: " 1 "24" 2 "28" 3 "32" 4 "36" 5 "40" 6 "48") pos(6) r(1) ) ///	   
		xtitle("Intensity of pandemic") ytitle(Predicted probability) ///
		title("Uncertain fertility intentions")
graph export "$tables/Figure_A4.wmf", replace as(wmf)
graph export "$tables/Figure_A4.png", replace as(png)



** FIGURE A6
*----------------------------

foreach suf in yes  unc{
	
local title = cond("`suf'"=="yes", "Positive fertility intentions" , ///
			"Uncertain fertility intentions")
	
twoway (connect pdp_`suf' deaths if f1_value =="1-Partner") ///
       (connect pdp_`suf' deaths if f1_value =="2-Married") ///
	   if feature2 =="std_tv_deaths" & feature1 == "partner" , ///
	   legend(order(1 "Partner" 2 "Married") pos(6) r(1)  ) ///
	   xtitle("Intensity of pandemic") ytitle(Predicted probability) title("`title'") ///
	   name(gr_`suf'1, replace)

		
		
		
twoway (connect pdp_`suf' deaths if f1_value =="1-Primary") ///
       (connect pdp_`suf' deaths if f1_value =="2-High-School") ///
       (connect pdp_`suf' deaths if f1_value =="3-Bachelor") ///
        (connect pdp_`suf' deaths if f1_value =="4-More than BA") ///
	   if feature2 =="std_tv_deaths" & feature1 == "educ_own" , ///
		legend(order(1 "Primary" 2 "High-School" 3 "Bachelor" 4 "More than BA") pos(6) r(1)  ) ///
		name(gr_`suf'2, replace) ///
		xtitle("Intensity of pandemic") ytitle("Predicted probability") ///
			   title("`title'")	   
	

twoway (connect pdp_`suf' deaths if f2_value =="1-No") ///
       (connect pdp_`suf' deaths if f2_value =="2-Intermediate") ///
       (connect pdp_`suf' deaths if f2_value =="3-Yes") ///
        	   if feature1 =="std_tv_deaths" & feature2 == "religious" , ///
		legend(order(- "Religious person: " 1 "No" 2 "Intermediate" 3 "Yes") pos(6) r(1) )  ///	   
		xtitle("Intensity of pandemic") ytitle(Predicted probability) name(gr_`suf'3, replace) ///
		title("`title'")	 
		}
 
	  

* Panel (a) 
	graph di gr_yes1
	graph export "$tables/Figure_A6_pa.wmf" , replace as(wmf)
	graph export "$tables/Figure_A6_pa.png" , replace as(png)
	
* Panel (b) 
	graph di gr_yes2
	graph export "$tables/Figure_A6_pb.wmf" , replace as(wmf)
	graph export "$tables/Figure_A6_pb.png" , replace as(png)

* Panel (c) 
	graph di gr_yes3
	graph export "$tables/Figure_A6_pc.wmf" , replace as(wmf)
    graph export "$tables/Figure_A6_pc.png" , replace as(png)
	
 
 

