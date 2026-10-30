*-----------------------------------*
*		Paths and programs			*
*-----------------------------------*


** Paths
*---------------------------------

global code      `c(pwd)'						// Replace with actual location
global data_raw "$code/../raw_data/"			// Folder with original GGS II data
global output   "$code/../replication_output"   // For intermediate outputs
global tables   "$code/../replication_tables"   // For tables and figures




** Programs
*--------------------------------

ssc install scheme-burd
set scheme burd

net install  grc1leg , from(http://www.stata.com/users/vwiggins)

** User-written commands
*----------------------------------

capture mata: mata drop get_info()
mata: 
void get_info  (string scalar matname , scalar coln )
	{
	real matrix b, R, dim1, dim2, range1, range2
	real scalar nV1, nV2, i1 , i2 , i_f

	b=st_matrix(matname)
	nV1    = rows(uniqrows(b[,1]))
	nV2    = rows(uniqrows(b[,2]))
 

	R = colshape(b[,coln],  nV2)
	
	dim1 = rowminmax(R)
	range1  = 0.25 :*(dim1[,2] - dim1[,1])
	i1 =  sqrt(variance(range1  )) 
	
	dim2 = colminmax(R)'
 	range2  = 0.25 :*(dim2[,2] - dim2[,1])
	i2 =  sqrt(variance(range2  )) 
	
	i_f = (i1 + i2)/2
	st_numscalar("r(if)", i_f)
	st_matrix("r(range1)", range1)
	st_matrix("r(range2)", range2)	
	}
	end
	
	
		
capture program drop extract_info	
program define extract_info , rclass
syntax anything   [, coln( integer 5)]


mata: get_info("`anything'" , `coln')
return scalar if =  r(if)

mat r1 = r(range1)
return matrix range1 = r1 

mat r2 = r(range2)
return matrix range2 = r2  

end