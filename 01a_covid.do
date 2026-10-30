*---------------------------------------------*
*		COVID
*---------------------------------------------*


clear
import delimited "$data_raw/COVID/WHO-COVID-19-global-data.csv" , clear

/* SOURCE
	https://data.who.int/dashboards/covid19/data
*/

keep if inlist(country, "Germany", "Estonia", "Finland" , "Norway" , "Sweden") ///
		| inlist(country, "Czechia", "Croatia" ,   "Denmark" , "Austria") ///
		| strpos(country, "United Kingdom") !=0 | strpos(country, "Netherla") !=0


ren date_reported date_str
ren country_code eu_code
replace eu_code = "UK" if eu_code =="GB"

gen date = date(date_str, "YMD")
format date %td

gen month_date = mofd(date)
format month_date %tm

gen year = year(date)
gen month_year = month(date)

collapse (sum) new_cases new_deaths (max) cumulative_cases  (first) month_year year ///
		, by(month_date eu_code) 

		
encode eu_code , gen(cn) 		
xtset cn month_date

** Standardizing values
foreach var in cases deaths{
	egen base_`var' = max(new_`var'*(month_date == ym(2021,01))) , by(eu_code) 
	gen reg_`var' = new_`var'/base_`var'	
	
	egen mean_`var' = mean(new_`var') , by(eu_code)
	egen sd_`var'   = sd(new_`var')   , by(eu_code)

	gen std_`var'   = (new_`var' - mean_`var')/sd_`var' 
	}
 
 
** Standardizing up to that point

bys eu_code (month_date): gen nobs = _n
foreach var in cases deaths{
		
	bys eu_code (month_date): gen sum_`var' = sum(new_`var') 
	gen mean_tv_`var' = sum_`var' /nobs 
	
	bys eu_code (month_date):  gen dev_`var' = (new_`var' - mean_tv_`var')*(new_`var' - mean_tv_`var'[_n-1])
	bys eu_code (month_date):  gen ssq_`var' =  sum(dev_`var')
	
	gen sd_tv_`var' =  sqrt(ssq_`var'/(nobs-1) ) 
	gen std_tv_`var'   = (new_`var' - mean_tv_`var')/sd_tv_`var'

	
	drop  sum_`var'  dev_`var'  ssq_`var' sd_tv_`var'
	}
 
 
save ../replication_data/data_covid , replace

 